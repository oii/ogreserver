from __future__ import absolute_import

import os

# import Flask-Uploads
from flask.ext.uploads import UploadSet, ALL, configure_uploads


def init_uploads(app):
    # setup Flask-Upload for ebook uploads
    ebooks = UploadSet('ebooks', extensions=app.config['EBOOK_DEFINITIONS'].keys())

    # setup log file uploads
    logs = UploadSet('logs', ALL)

    # ensure directory exists
    if not os.path.exists(app.config['UPLOADED_EBOOKS_DEST']):
        os.makedirs(app.config['UPLOADED_EBOOKS_DEST'])

    configure_uploads(app, (ebooks, logs))
    return ebooks, logs
