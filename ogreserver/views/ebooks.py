from __future__ import absolute_import
from __future__ import unicode_literals

from flask import current_app as app

from flask import Blueprint, request, jsonify, redirect, render_template
from flask.ext.security.decorators import login_required

from ..models.datastore import DataStore
from ..models.search import Search
from ..utils import request_wants_json

bp_ebooks = Blueprint('ebooks', __name__)


@bp_ebooks.route('/list', methods=['GET', 'POST'])
@bp_ebooks.route('/list/<terms>')
@bp_ebooks.route('/list/<terms>/')
@bp_ebooks.route('/list/<terms>/<int:pagenum>')
@login_required
def listing(terms=None, pagenum=1):
    # redirect search POST onto a nice GET url
    if request.method == 'POST':
        return redirect('/list/{}'.format(request.form['s']), code=303)

    # map single plus char onto an empty search
    if terms == '+':
        terms = None

    search = Search(app.whoosh, app.config['SEARCH_PAGELEN'])

    if request_wants_json(request):
        # return single page as JSON
        return jsonify(search.query(terms, pagenum=pagenum))
    else:
        # return all pages upto pagenum as HTML
        rs = search.query(terms, pagenum=pagenum, allpages=True)
        return render_template('list.html', ebooks=rs)


@bp_ebooks.route('/view/<ebook_id>')
@login_required
def view(ebook_id):
    ds = DataStore(app.config, app.logger)
    ebook = ds.load_ebook(ebook_id)
    return render_template('view.html', ebook=ebook)


@bp_ebooks.route('/download/<ebook_id>', defaults={'version_id': None, 'fmt': None})
@bp_ebooks.route('/download/<ebook_id>/<version_id>', defaults={'fmt': None})
@bp_ebooks.route('/download/<ebook_id>/<version_id>/<fmt>')
@login_required
def download(ebook_id, version_id=None, fmt=None):
    ds = DataStore(app.config, app.logger)
    return redirect(ds.get_ebook_url(ebook_id, version_id=version_id, fmt=fmt))
