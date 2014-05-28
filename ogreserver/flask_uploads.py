from __future__ import absolute_import

# import Flask-Uploads
from flask.ext.uploads import UploadSet, ALL, configure_uploads


def init_app(app):
    # setup Flask-Upload
    uploads = UploadSet('ebooks', ALL)
    configure_uploads(app, (uploads))

    return uploads
