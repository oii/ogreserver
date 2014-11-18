from __future__ import absolute_import
from __future__ import unicode_literals

from flask import current_app as app

from flask import Blueprint, request, redirect, render_template
from flask.ext.login import login_required

from ..models.datastore import DataStore

bp_ebooks = Blueprint('ebooks', __name__)


@bp_ebooks.route('/list', methods=['GET', 'POST'])
@login_required
def listing():
    ds = DataStore(app.config, app.logger, app.whoosh)
    s = request.args.get('s')
    if s:
        rs = ds.search(s)
    else:
        rs = ds.search()

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
