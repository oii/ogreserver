from __future__ import absolute_import
from __future__ import unicode_literals

import os

from flask import current_app as app
from flask import render_template

import requests

from .extensions.database import setup_db_session

from .exceptions import (ConversionFailedError, EbookNotFoundOnS3Error, S3DatastoreError,
                         AmazonHttpError, RethinkdbError)
from .models.amazon import AmazonAPI
from .models.datastore import DataStore
from .models.goodreads import GoodreadsAPI


@app.celery.task(queue='normal', rate_limit='1/s')
def query_ebook_metadata(ebook_data):
    """
    Set and validate ebook metadata, authors, title etc. by querying external APIs
    """
    with app.app_context():
        am = AmazonAPI(
            app.logger,
            app.config['AWS_ADVERTISING_API_ACCESS_KEY'],
            app.config['AWS_ADVERTISING_API_SECRET_KEY'],
            app.config['AWS_ADVERTISING_API_ASSOCIATE_TAG'],
            match_threshold=app.config['AMAZON_FUZZ_THRESHOLD']
        )

        try:
            # query Amazon affiliate API first
            am_data = am.search(
                asin=ebook_data['meta']['asin'],
                author=ebook_data['author'],
                title=ebook_data['title']
            )
            app.logger.debug(am_data)
        except AmazonHttpError:
            # retry the current task
            query_ebook_metadata.retry(
                countdown=1, max_retries=3, throw=False, **{'ebook_data': ebook_data}
            )
            return

        author = title = None

        if am_data:
            # extract image URL from Amazon data
            ebook_data['image_url'] = am_data['image_url']

            # store all Amazon data in ebook meta
            ebook_data['meta']['amazon'] = am_data

            # variables for further Goodreads API call
            author = am_data['author']
            title = am_data['title']

        # query Goodreads API
        gr = GoodreadsAPI(app.logger, app.config['GOODREADS_API_KEY'])
        gr_data = gr.search(
            isbn=ebook_data['meta']['isbn'],
            author=author or ebook_data['author'],
            title=title or ebook_data['title']
        )
        app.logger.debug(gr_data)

        if gr_data:
            # extract first author from Goodreads
            try:
                ebook_data['author'] = gr_data['authors'][0]['name']
            except Exception:
                pass

            # import other fields from Goodreads
            for field in ('title', 'publisher'):
                try:
                    ebook_data[field] = gr_data[field]
                except Exception:
                    pass

            # store all Goodreads data in ebook meta
            ebook_data['meta']['goodreads'] = gr_data

        try:
            # update the datastore
            ds = DataStore(app.config, app.logger)
            ds.update_ebook(ebook_data['ebook_id'], ebook_data)
        except RethinkdbError:
            app.logger.critical(
                'Failed updating ebook metadata: {}'.format(ebook_data['ebook_id'])
            )


@app.celery.task(queue='high')
def store_ebook(ebook_id, filename, file_hash, fmt, username):
    """
    Store an ebook in the datastore
    """
    with app.app_context():
        # initialise the DB connection in our fake app context
        setup_db_session(app)

        try:
            # create the datastore
            ds = DataStore(app.config, app.logger)

            # local path of uploaded file
            filepath = os.path.join(app.config['UPLOADED_EBOOKS_DEST'], os.path.basename(filename))

            # store the file into S3
            ds.store_ebook(ebook_id, file_hash, filepath, username)

        except S3DatastoreError as e:
            app.logger.error('Failed uploading {} with {}'.format(file_hash, e))

        finally:
            # always delete local files who share the same hash in their filename
            # (these are repeat uploads, uniquely named by Flask-Uploads)
            for fn in os.listdir(app.config['UPLOADED_EBOOKS_DEST']):
                if fn.startswith(file_hash):
                    os.remove(os.path.join(app.config['UPLOADED_EBOOKS_DEST'], fn))


@app.celery.task(queue='normal')
def conversion_search():
    """
    Search for ebooks which are missing key formats epub & mobi
    """
    with app.app_context():
        # late import to prevent circular import
        from .models.conversion import Conversion
        conversion = Conversion(app.config, DataStore(app.config, app.logger), flask_app=app)
        conversion.search()


@app.celery.task(queue='low')
def convert(ebook_id, version_id, original_filename, dest_fmt):
    """
    Convert an ebook to other formats, currently mobi & epub
    """
    with app.app_context():
        # late import to prevent circular import
        from .models.conversion import Conversion
        conversion = Conversion(app.config, DataStore(app.config, app.logger), flask_app=app)

        try:
            conversion.convert(ebook_id, version_id, original_filename, dest_fmt)

        except EbookNotFoundOnS3Error:
            app.logger.warning('Book missing from S3 ({}, {}, {}, {})'.format(
                ebook_id, version_id, original_filename, dest_fmt
            ))
        except ConversionFailedError as e:
            app.logger.error('Conversion failed ({}, {}, {}, {})'.format(
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
