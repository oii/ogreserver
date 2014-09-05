from __future__ import absolute_import

import os
import json
import subprocess

from .extensions.celery import celery
from .extensions.database import get_db

from .models.datastore import DataStore, S3DatastoreError


@celery.task
def store_ebook(ebook_id, file_hash, fmt):
    """
    Store an ebook in the datastore
    """
    # import the Flask app and spoof a context
    from .runflask import app
    with app.test_request_context():
        filepath = None

        # remove the Flask logger; test_request_context provides DebugLogger
        del(app.logger.handlers[0])

        # initialise the DB connection in our fake app context
        get_db(app)

        try:
            # create the datastore & generate a nice filename
            ds = DataStore(app.config, app.logger)
            filename = ds.generate_filename(file_hash)

            # storage path
            filepath = os.path.join(app.config['UPLOADED_EBOOKS_DEST'], '{}.{}'.format(file_hash, fmt))

            # store the file into S3
            if ds.store_ebook(ebook_id, file_hash, filename, filepath, fmt):
                app.logger.info('{} was uploaded'.format(filename))
            else:
                app.logger.info('{} exists on S3'.format(filename))

        except S3DatastoreError as e:
            app.logger.error('Failed uploading {} with {}'.format(filename, e))

        finally:
            # always delete local file
            if filepath is not None and os.path.exists(filepath):
                os.remove(filepath)


@celery.task(queue="conversion")
def convert_ebook(sdbkey, source_filepath, dest_fmt):
    """
    Convert an ebook to another format, and push to datastore
    """
    pass
    #source_filepath = "%s/%s.%s" % (app.config['UPLOADED_EBOOKS_DEST'], file_hash, fmt)

    #for convert_fmt in app.config['EBOOK_FORMATS']:
    #    if fmt == convert_fmt:
    #        continue

    #    dest_filepath = "%s/%s.%s" % (app.config['UPLOADED_EBOOKS_DEST'], file_hash, fmt)

    #    meta = subprocess.Popen(['ebook-convert', source_filepath, ], 
    #                            stdout=subprocess.PIPE).communicate()[0]

    #if store == True:
    #    if user_id == None:
    #        raise Exception("user_id must be supplied to convert_ebook when store=True")

    #    store_ebook.delay(user_id, sdbkey, file_hash, fmt)


# TODO nightly which recalculates book ratings: 
#      10% of entire database per night (LOG the total and time spent)

# TODO nightly which check books are stored on S3 and updates SDB 

