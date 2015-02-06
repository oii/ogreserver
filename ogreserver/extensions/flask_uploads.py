from __future__ import absolute_import

# import Flask-Uploads
from flask.ext.uploads import UploadSet, ALL, configure_uploads


def init_uploads(app):
    # setup Flask-Upload for ebook uploads
    ebooks = UploadSet('ebooks', extensions=app.config['EBOOK_DEFINITIONS'].keys())

    # setup log file uploads
    logs = UploadSet('logs', ALL)

    configure_uploads(app, (ebooks, logs))
    return ebooks, logs
