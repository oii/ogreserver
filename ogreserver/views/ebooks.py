from __future__ import absolute_import
from __future__ import unicode_literals

import pyaml

from flask import current_app as app

from flask import g, Blueprint, request, jsonify, redirect, url_for
from flask.ext.security.decorators import login_required
from werkzeug.exceptions import abort

from ..forms.search import SearchForm
from ..models.datastore import DataStore
from ..models.search import Search
from ..utils import render_template, request_wants_json

bp_ebooks = Blueprint('ebooks', __name__)


@bp_ebooks.route('/list/', methods=['GET', 'POST'])
@bp_ebooks.route('/list/<int:pagenum>/')
@login_required
def listing(pagenum=1):
    search_form = SearchForm(request.args)
    search_form.data['pagenum'] = pagenum

    search = Search(app.whoosh, pagelen=app.config.get('SEARCH_PAGELEN', 20))

    if request_wants_json(request):
        # return single page as JSON
        return jsonify(search.query(**search_form.data))
    else:
        # return all pages upto pagenum as HTML
        search_form.data['allpages'] = True
        rs = search.query(**search_form.data)
        return render_template('list.html', ebooks=rs, search_form=search_form)


@bp_ebooks.route('/ebook/<ebook_id>/')
@login_required
def detail(ebook_id):
    ds = DataStore(app.config, app.logger)
    ebook = ds.load_ebook(ebook_id)

    if ebook is None:
        abort(404)

    # display original source on ebook detail page
    ebook['provider'] = ebook['meta']['source']['provider']

    # absolute URL to ebook cover image
    ebook['image_url'] = '{}/{}/{}-0.jpg'.format(
        app.config['STATIC_BASE_URL'],
        app.config['STATIC_S3_BUCKET'],
        ebook['ebook_id']
    )

    if g.user.advanced:
        # if user has advanced flag set on their profile,
        # render extra ebook metadata as YAML so it looks pretty
        ebook['rawmeta'] = {}
        for source in ('source', 'amazon', 'goodreads'):
            if source in ebook['meta']:
                ebook['rawmeta'][source] = pyaml.dump(ebook['meta'][source]).replace("'", '')

    return render_template('ebook_detail.html', ebook=ebook)


@bp_ebooks.route('/ebook/<ebook_id>/curated/<int:state>')
@login_required
def set_curated(ebook_id, state):
    ds = DataStore(app.config, app.logger)
    ds.set_curated(ebook_id, state)
    return redirect(url_for('.detail', ebook_id=ebook_id))


@bp_ebooks.route('/download/<ebook_id>/', defaults={'version_id': None, 'fmt': None})
@bp_ebooks.route('/download/<ebook_id>/<version_id>/', defaults={'fmt': None})
@bp_ebooks.route('/download/<ebook_id>/<version_id>/<fmt>/')
@login_required
def download(ebook_id, version_id=None, fmt=None):
    ds = DataStore(app.config, app.logger)
    return redirect(ds.get_ebook_download_url(ebook_id, version_id=version_id, fmt=fmt))
