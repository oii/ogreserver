from __future__ import absolute_import
from __future__ import unicode_literals

from flask import current_app as app
from flask import Blueprint, redirect
from flask.ext.security.decorators import login_required

from ..models.datastore import DataStore

bp_download = Blueprint('download', __name__, url_prefix='/download')


@bp_download.route('/ogreclient')
def ogreclient():
    # supply the latest DRM tools to the client
    url = 'https://s3-{}.amazonaws.com/{}/ogreclient-{}.zip'.format(
        app.config['AWS_REGION'],
        app.config['DIST_S3_BUCKET'].format(app.config['env']),
        app.config['OGRECLIENT_VERSION']
    )
    return redirect(url, code=302)


@bp_download.route('/bitbar')
def bitbar():
    # supply the latest DRM tools to the client
    url = 'https://s3-{}.amazonaws.com/{}/BitBarDistro.zip'.format(
        app.config['AWS_REGION'],
        app.config['DIST_S3_BUCKET'].format(app.config['env'])
    )
    return redirect(url, code=302)


@bp_download.route('/ebook/<ebook_id>/', defaults={'version_id': None, 'fmt': None})
@bp_download.route('/ebook/<ebook_id>/<version_id>/', defaults={'fmt': None})
@bp_download.route('/ebook/<ebook_id>/<version_id>/<fmt>/')
@login_required
def ebook(ebook_id, version_id=None, fmt=None):
    ds = DataStore(app.config, app.logger)
    return redirect(
        ds.get_ebook_download_url(ebook_id, version_id=version_id, fmt=fmt)
    )
