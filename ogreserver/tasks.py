from __future__ import absolute_import
from __future__ import unicode_literals

import os
import urllib

from flask import current_app as app, g
from flask import render_template

import requests
import whoosh

from celery.task import current

from boto.exception import S3ResponseError

from .extensions.database import setup_db_session
from .extensions.whoosh import init_whoosh

from .exceptions import (ConversionFailedError, EbookNotFoundOnS3Error, S3DatastoreError,
                         AmazonHttpError)
from .models.amazon import AmazonAPI
from .models.conversion import Conversion
from .models.ebook import Ebook, Version
from .models.goodreads import GoodreadsAPI
from .models.search import Search
from .models.user import User
from .stores import ebooks as ebook_store
from .stores import s3 as s3_store
from .utils.generic import make_temp_directory
from .utils.s3 import connect_s3


@app.celery.task(queue='high', rate_limit='1/s')
def query_ebook_metadata(ebook_id):
    """
    Set and validate ebook metadata, authors, title etc. by querying external APIs

    params:
        ebook_id (int)   id of new Ebook object
    """
    with app.app_context():
        # initialise the DB connection in our fake app context
        setup_db_session(app)

        ebook = Ebook.query.get(ebook_id)

        app.logger.info('{} - Querying metadata for {}'.format(ebook, ebook.asin))

        am = AmazonAPI(
            app.config['AWS_ADVERTISING_API_ACCESS_KEY'],
            app.config['AWS_ADVERTISING_API_SECRET_KEY'],
            app.config['AWS_ADVERTISING_API_ASSOCIATE_TAG'],
            match_threshold=app.config.get('AMAZON_FUZZ_THRESHOLD', 50)
        )

        try:
            # query Amazon affiliate API first
            am_data = am.search(
                asin=ebook.asin,
                author=ebook.author,
                title=ebook.title
            )
            app.logger.debug('{} {}'.format(ebook, am_data))

        except AmazonHttpError:
            # retry the current task
            query_ebook_metadata.retry(
                countdown=1, max_retries=3, throw=False, **{'ebook_id': ebook.id}
            )
            return

        if am_data:
            app.logger.info('{} - Amazon data for ASIN {}'.format(ebook, am_data['asin']))

            # store all Amazon data in ebook meta
            ebook_store.append_ebook_metadata(ebook, 'amazon', am_data)

            # copy ASIN into top-level ebook meta
            ebook.asin = am_data['asin']

            # variables for further Goodreads API call
            ebook.author = am_data['author']
            ebook.title = am_data['title']

            # start task to upload Amazon image to S3
            image_upload.delay(ebook.id, am_data['image_url'])

        # query Goodreads API
        gr = GoodreadsAPI(app.config['GOODREADS_API_KEY'])
        gr_data = gr.search(
            isbn=ebook.isbn,
            author=ebook.author,
            title=ebook.title
        )
        app.logger.debug('{} {}'.format(ebook, gr_data))

        if gr_data:
            app.logger.info('{} - Goodreads data for ISBN {}'.format(ebook, ebook.isbn))

            # extract first author from Goodreads
            try:
                ebook.author = gr_data['authors'][0]['name']
            except Exception:
                pass

            # import other fields from Goodreads
            if 'title' in gr_data:
                ebook.title = gr_data['title']
            if 'publisher' in gr_data:
                ebook.publisher = gr_data['publisher']
            if 'num_pages' in gr_data:
                ebook.num_pages = gr_data['num_pages']
            if 'isbn' in gr_data:
                ebook.isbn = gr_data['isbn']
            if 'isbn13' in gr_data:
                ebook.isbn13 = gr_data['isbn13']
            if 'average_rating' in gr_data:
                ebook.average_rating = gr_data['average_rating']

            # store all Goodreads data in ebook meta
            ebook_store.append_ebook_metadata(ebook, 'goodreads', gr_data)

        # write directly back to the DB
        g.db_session.add(ebook)
        g.db_session.commit()


@app.celery.task(queue='low')
def image_upload(ebook_id, image_url):
    """
    Upload book image to S3. Images are named by ebook_id, which means they'll
    appear in the frontend when available.
    """
    with app.app_context():
        # fetch remote image into temp directory
        with make_temp_directory() as tmpdir:
            try:
                res = urllib.urlretrieve(
                    image_url, os.path.join(tmpdir, 'image_file')
                )
            except KeyError:
                app.logger.error('No image available: {}'.format(image_url))
            except Exception as e:
                app.logger.error('Failed retrieving image {}: {}'.format(image_url, e))
                return

            # generate new S3 filename
            filename = '{}-0.jpg'.format(ebook_id)

            try:
                # upload to S3
                s3 = connect_s3(app.config)
                bucket = s3.get_bucket(app.config['STATIC_S3_BUCKET'].format(app.config['env']))
                k = bucket.new_key(filename)
                k.content_type = 'image/jpeg'
                k.set_contents_from_filename(res[0], policy='public-read')

            except S3ResponseError as e:
                app.logger.error('Error uploading to S3: {}'.format(e))
                return


@app.celery.task(queue='high')
def index_for_search(ebook_id):
    """
    Add ebook to the Whoosh search index
    """
    with app.app_context():
        # initialise the DB connection in our fake app context
        setup_db_session(app)

        ebook = Ebook.query.get(ebook_id)

        try:
            # create search class and index
            search = Search(init_whoosh(app), pagelen=app.config.get('SEARCH_PAGELEN', 20))
            search.index_for_search({
                'ebook_id': ebook.id,
                'author': ebook.author,
                'title': ebook.title,
                'is_curated': ebook.is_curated,
                'is_fiction': not ebook.is_non_fiction,
            })

        except whoosh.writing.LockError:
            # if index is unavailable try again in 10 secs
            current.retry(
                kwargs={'ebook_id': ebook_id},
                countdown=10,
            )


@app.celery.task(queue='high')
def upload_ebook(ebook_id, filename, file_hash, fmt, username):
    """
    Upload an ebook to S3
    """
    with app.app_context():
        # initialise the DB connection in our fake app context
        setup_db_session(app)

        try:
            # local path of uploaded file
            filepath = os.path.join(app.config['UPLOADED_EBOOKS_DEST'], os.path.basename(filename))

            # determine ebook file content type
            content_type = None
            if fmt in app.config['EBOOK_CONTENT_TYPES']:
                content_type = app.config['EBOOK_CONTENT_TYPES'][fmt]

            user = User.query.filter_by(username=username).one()

            # store the file into S3
            s3_store.upload_ebook(ebook_id, file_hash, filepath, user, content_type)

        except S3DatastoreError as e:
            app.logger.error('Failed uploading {} with {}'.format(file_hash, e))

        finally:
            # always delete local files who share the same hash in their filename
            # (these are repeat uploads, uniquely named by Flask-Uploads)
            for fn in os.listdir(app.config['UPLOADED_EBOOKS_DEST']):
                if fn.startswith(file_hash):
                    os.remove(os.path.join(app.config['UPLOADED_EBOOKS_DEST'], fn))


@app.celery.task(queue='low')
def conversion_search():
    """
    Search for ebooks which are missing key formats epub & mobi
    """
    with app.app_context():
        # initialise the DB connection in our fake app context
        setup_db_session(app)

        conversion = Conversion(app.config)
        conversion.search(app.config['NUM_EBOOKS_FOR_CONVERT'])


@app.celery.task(queue='low')
def convert(ebook_id, version_id, original_filename, dest_fmt):
    """
    Convert an ebook to other formats, currently mobi & epub
    """
    with app.app_context():
        # initialise the DB connection in our fake app context
        setup_db_session(app)

        conversion = Conversion(app.config)

        try:
            version = Version.query.get(version_id)

            app.logger.debug('Converting {} to {} ({}) '.format(
                original_filename, dest_fmt, version_id
            ))
            conversion.convert(ebook_id, version, original_filename, dest_fmt)

        except EbookNotFoundOnS3Error:
            app.logger.warning('Book missing from S3 ({}/{}, {}, {})'.format(
                ebook_id, version_id, original_filename, dest_fmt
            ))
        except ConversionFailedError as e:
            app.logger.error('Conversion failed ({}/{}, {}, {})'.format(
                ebook_id, version_id, original_filename, dest_fmt
            ))
            app.logger.debug(e)


@app.celery.task(queue='high')
def send_mail(recipient, subject, template, **context):
    """
    Send an email via Mailgun

    curl -s --user 'api:YOUR_API_KEY' \
        https://api.mailgun.net/v2/YOUR_DOMAIN_NAME/messages \
        -F from='Excited User <YOU@YOUR_DOMAIN_NAME>' \
        -F to='foo@example.com' \
        -F subject='Hello' \
        -F text='Testing some Mailgun awesomness!' \
        --form-string html='<html>HTML version of the body</html>'
    """
    with app.app_context():
        domain = app.config['HOSTNAME']
        api_key = app.config['MAILGUN_API_KEY']
        sender = app.config['SECURITY_EMAIL_SENDER']

        parts = {}

        # render both the text & html templates for the mime message
        for part in ('txt', 'html'):
            parts[part] = render_template(
                'security/email/{}.{}'.format(template, part), **context
            )

        # send the email via Mailgun's API
        resp = requests.post(
            'https://api.mailgun.net/v2/{}/messages'.format(domain),
            auth=('api', api_key),
            data={
                'from': sender,
                'to': recipient,
                'subject': subject,
                'text': parts['txt'],
                'html': parts['html'],
            }
        )
        app.logger.info("'{}' email sent to {}, with id='{}'".format(
            subject,
            recipient,
            resp.json()['id']
        ))
