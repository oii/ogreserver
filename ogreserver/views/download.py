from __future__ import absolute_import
from __future__ import unicode_literals

from flask import current_app as app
from flask import Blueprint, redirect


bp_download = Blueprint('download', __name__, url_prefix='/download')


@bp_download.route('/ogreclient')
def ogreclient():
    # supply the latest DRM tools to the client
    url = 'https://s3-{}.amazonaws.com/{}/ogreclient-{}.zip'.format(
        app.config['AWS_REGION'],
        app.config['DIST_S3_BUCKET'],
        app.config['OGRECLIENT_VERSION']
    )
    return redirect(url, code=302)
