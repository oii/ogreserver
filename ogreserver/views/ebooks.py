from __future__ import absolute_import
from __future__ import unicode_literals

import pyaml

from flask import current_app as app

from flask import g, Blueprint, make_response, request, redirect, url_for
from flask.ext.security.decorators import login_required
from werkzeug.exceptions import abort

from ..exceptions import NoMoreResultsError
from ..forms.search import SearchForm
from ..models.datastore import DataStore
from ..models.search import Search
from ..utils.flask import render_template

bp_ebooks = Blueprint('ebooks', __name__)


@bp_ebooks.route('/list/', methods=['GET', 'POST'])
@bp_ebooks.route('/list/<int:pagenum>/')
@login_required
def listing(pagenum=None):
    if not pagenum:
        pagenum = int(request.args.get('pagenum', 1))

    query_data = {
        's': request.args.get('s'),
        'is_curated': request.args.get('is_curated'),
        'is_fiction': request.args.get('is_fiction'),
        'pagenum': pagenum,
        'allpages': True,
    }

    rs = None

    try:
        search = Search(app.whoosh, pagelen=app.config.get('SEARCH_PAGELEN', 10))
        rs = search.query(**query_data)
    except NoMoreResultsError:
        if pagenum > 1:
            # redirect to /list with no page number
            return redirect(url_for('ebooks.listing'))

    return render_template(
        'list.html',
        ebooks=rs or [],
        pagenum=pagenum,
        search_form=SearchForm(request.args)
    )


@bp_ebooks.route('/list-fragment/')
@login_required
def listing_fragment():
    pagenum = int(request.args['pagenum'])

    query_data = {
        's': request.args['s'],
        'is_curated': True,
        'is_fiction': True,
        'pagenum': pagenum,
        'allpages': False,
    }

    try:
        search = Search(app.whoosh, pagelen=app.config.get('SEARCH_PAGELEN', 10))
        rs = search.query(**query_data)
    except NoMoreResultsError:
        return ''

    resp = make_response(render_template(
        'list_fragment.html',
        ebooks=rs,
        search_text=request.args['s'],
        pagenum=pagenum,
        search_form=SearchForm(**query_data)
    ))
    # use intercooler's history rewrite header
    resp.headers['X-IC-PushURL'] = '/list/{}/#{}'.format(pagenum, rs['results'][0]['ebook_id'][0:7])
    return resp


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
        app.config['STATIC_S3_BUCKET'].format(app.config['env']),
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
