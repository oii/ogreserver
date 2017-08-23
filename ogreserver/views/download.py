from __future__ import absolute_import
from __future__ import unicode_literals

from datadog import statsd
from flask import current_app as app
from flask import Blueprint, redirect
from flask_security.decorators import login_required

from ..stores import s3 as s3_store

bp_download = Blueprint('download', __name__, url_prefix='/download')


@bp_download.route('/ogreclient')
@statsd.timed()
def ogreclient():
    statsd.increment('views.download.ogreclient', 1)

    # supply the latest DRM tools to the client
    url = 'https://s3-{}.amazonaws.com/{}/ogre-{}'.format(
        app.config['AWS_REGION'],
        app.config['DIST_S3_BUCKET'].format(app.config['env']),
        app.config['OGRECLIENT_VERSION']
    )
    return redirect(url, code=302)


@bp_download.route('/bitbar')
@statsd.timed()
def bitbar():
    statsd.increment('views.download.bitbar', 1)

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
@statsd.timed()
def ebook(ebook_id, version_id=None, fmt=None):
    statsd.increment('views.download.ebook', 1)

    return redirect(
        s3_store.get_ebook_download_url(ebook_id, version_id=version_id, fmt=fmt)
    )
