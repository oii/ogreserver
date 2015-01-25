from __future__ import absolute_import
from __future__ import unicode_literals

import os

from flask import current_app as app
from flask import render_template

import requests

from .extensions.database import setup_db_session

from .exceptions import ConversionFailedError, EbookNotFoundOnS3Error, S3DatastoreError
from .models.datastore import DataStore


@app.celery.task
def store_ebook(ebook_id, file_hash, fmt, username):
    """
    Store an ebook in the datastore
    """
    with app.app_context():
        filepath = None

        # initialise the DB connection in our fake app context
        setup_db_session(app)

        try:
            # create the datastore & generate a nice filename
            ds = DataStore(app.config, app.logger)
            filename = ds.generate_filename(file_hash)

            # storage path
            filepath = os.path.join(app.config['UPLOADED_EBOOKS_DEST'], '{}.{}'.format(file_hash, fmt))

            # store the file into S3
            if ds.store_ebook(ebook_id, file_hash, filename, filepath, fmt, username):
                app.logger.info('{} was uploaded'.format(filename))
                return True
            else:
                app.logger.info('{} exists on S3'.format(filename))
                return False

        except S3DatastoreError as e:
            app.logger.error('Failed uploading {} with {}'.format(filename, e))

        finally:
            # always delete local file
            if filepath is not None and os.path.exists(filepath):
                os.remove(filepath)


@app.celery.task
def conversion_search():
    """
    Search for ebooks which are missing key formats epub & mobi
    """
    with app.app_context():
        # late import to prevent circular import
        from .models.conversion import Conversion
        conversion = Conversion(app.config, DataStore(app.config, app.logger))
        conversion.search()


@app.celery.task(queue="conversion")
def convert(ebook_id, version_id, original_filename, dest_fmt):
    """
    Convert an ebook to other formats, currently mobi & epub
    """
    with app.app_context():
        # late import to prevent circular import
        from .models.conversion import Conversion
        conversion = Conversion(app.config, DataStore(app.config, app.logger))

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


@app.celery.task
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
        # celery logs on stdout
        print "'{}' email sent to {}, with id='{}'".format(
            subject,
            recipient,
            resp.json()['id']
        )


# TODO nightly which recalculates book ratings: 
#      10% of entire database per night (LOG the total and time spent)

# TODO nightly which check books are stored on S3 and updates SDB 

# TODO nightly data corruption checks:
#   - never have multiple of same format attached to single version
