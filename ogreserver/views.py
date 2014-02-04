import base64
import fnmatch
import json
import os

from flask import g, current_app as app

from flask import request, redirect, session, abort, Blueprint
from flask import url_for, render_template, render_template_string, jsonify, make_response
from flask.ext.login import login_required, login_user, logout_user

from werkzeug.exceptions import Forbidden

from .utils import debug_print as dp

from forms.auth import LoginForm

from models.user import User
from models.datastore import DataStore
from models.reputation import Reputation
from models.log import Log

from tasks import store_ebook


views = Blueprint('views', __name__, static_folder='static')


# declare some error handler pages
@views.app_errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

@views.app_errorhandler(500)
def internal_error(error):
    g.db_session.rollback()
    return render_template('500.html'), 500


@views.route('/')
@login_required
def index():
    return redirect(url_for('views.home'))


@views.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        login_user(form.user)
        session['user_id'] = form.user.id
        return redirect(request.args.get('next') or url_for('views.index'))
    return render_template('login.html', form=form)


@views.route('/auth', methods=['POST'])
def auth():
    user = User.authenticate(
        username=request.form.get('username'),
        password=request.form.get('password')
    )
    if user == None:
        raise Forbidden
    else:
        return base64.b64encode(user.assign_auth_key())


@views.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('views.login'))


TEMPLATE_MD_START = (
    '{% extends "layout.html" %}'
    '{% block body %}'
    '{% filter markdown %}'
)
IMPROVE_URL = '\n[Improve this page](https://github.com/oii/ogre/blob/develop/ogreserver/docs/{}.md)'
TEMPLATE_MD_END = (
    '{% endfilter %}'
    '{% endblock %}'
)

@views.route("/docs")
@views.route("/docs/<path:doco>")
@login_required
def docs(doco=None):
    if doco is None:
        pages = []

        # TODO some kind of caching

        # iterate all the docs
        for root, dirs, files in os.walk('ogreserver/docs'):
            for filename in fnmatch.filter(files, '*.md'):
                # extract the summary from the markdown header
                summary = None
                with open(os.path.join(root, filename), 'r') as f:
                    for line in f:
                        if line == '\n':
                            break
                        elif line.startswith('Summary'):
                            summary = line[9:]

                pages.append({
                    'summary': summary,
                    'filename': os.path.splitext(filename)[0],
                })

        return render_template('docs.html', pages=pages)

    else:
        if not os.path.exists('ogreserver/docs/{}.md'.format(doco)):
            abort(404)

        # read in a markdown file from the docs
        with open('ogreserver/docs/{}.md'.format(doco), 'r') as f:
            # remove the markdown header
            content = []
            found_content = False
            for line in f:
                if found_content:
                    content += line
                elif line == '\n':
                    found_content = True

        # add a link to edit/improve this page
        improve_url = IMPROVE_URL.format(doco)

        # render a string for the Flask jinja template engine
        return render_template_string('{}{}{}{}'.format(
            TEMPLATE_MD_START,
            ''.join(content),
            improve_url,
            TEMPLATE_MD_END,
        ))


@views.route("/home")
@login_required
def home():
    return render_template("list.html")


@views.route('/list', methods=['GET', 'POST'])
@login_required
def list():
    ds = DataStore(app.config, app.whoosh)
    s = request.args.get('s')
    if s is None:
        rs = ds.list()
    else:
        rs = ds.search(s)
    return render_template('list.html', ebooks=rs)


@views.route('/ajax/rating/<pk>')
@login_required
def get_rating(pk):
    ds = DataStore(app.config)
    rating = ds.get_rating(pk)
    return jsonify({'rating': rating})


@views.route('/ajax/comment-count/<pk>')
@login_required
def get_comment_count(pk):
    ds = DataStore(app.config)
    comments = ds.get_comments(pk)
    return jsonify({'comments': len(comments)})


@views.route('/view')
@login_required
def view(sdbkey=None):
    ds = DataStore(app.config, app.whoosh)
    rs = ds.list()
    return render_template('view.html', ebooks=rs)


@views.route('/download/<pk>/', defaults={'fmt': None})
@views.route('/download/<pk>/<fmt>')
@login_required
def download(pk, fmt=None):
    ds = DataStore(app.config)
    return redirect(ds.get_ebook_url(pk, fmt))


@views.route('/download-dedrm/<auth_key>')
def download_dedrm(auth_key):
    check_auth(auth_key)

    # supply the latest DRM tools to the client
    with open('/var/pypiserver-cache/dedrm-6.0.7.tar.gz', 'r') as f:
        data = f.read()
        response = make_response(data)
        return response


@views.route('/post/<auth_key>', methods=['POST'])
def post(auth_key):
    user = check_auth(auth_key)

    # get the json payload
    data = json.loads(request.form.get('ebooks'))

    # stats log the upload
    Log.create(user.id, 'CONNECT', request.form.get('total'), user.session_api_key)

    # update the library
    ds = DataStore(app.config, app.whoosh)
    syncd_books = ds.update_library(data, user)

    # extract the subset of newly supplied books
    new_books = [item for key, item in syncd_books.items() if item['new'] is True]

    # extract the subset of books with missing ogre_id
    update_books = {
        key: item for key, item in syncd_books.items()
        if item['update'] is True
    }

    Log.create(user.id, 'NEW', len(new_books), user.session_api_key)

    # handle badge and reputation changes
    r = Reputation(user)
    r.new_ebooks(len(new_books))
    r.earn_badges()
    msgs = r.get_new_badges()

    # only request books for upload which are in client's current set
    incoming = [item['file_md5'] for item in data.values()]

    # query books missing from S3 and supply back to the client
    missing_books = ds.get_missing_books(username=user.username, md5_filter=incoming)
    return json.dumps({
        'ebooks_to_update': update_books,
        'ebooks_to_upload': missing_books,
        'messages': msgs
    })


@views.route('/confirm/<auth_key>', methods=['POST'])
def confirm(auth_key):
    check_auth(auth_key)

    # update a file's md5 hash
    current_file_md5 = request.form.get('file_md5')
    updated_file_md5 = request.form.get('new_md5')

    ds = DataStore(app.config)
    if ds.update_book_md5(current_file_md5, updated_file_md5):
        return 'ok'
    else:
        return 'fail'


@views.route('/upload/<auth_key>', methods=['POST'])
def upload(auth_key):
    user = check_auth(auth_key)

    # stats log the upload
    Log.create(user.id, 'UPLOADED', 1, user.session_api_key)

    dp(user.session_api_key, request.form.get('pk'), request.files['ebook'].content_length)

    # write uploaded ebook to disk, named as the hash and filetype
    app.uploads.save(request.files['ebook'], None, '{0}.{1}'.format(
        request.form.get('file_md5'), request.form.get('format')
    ))

    # let celery process the upload
    res = store_ebook.delay(
        user_id=user.id,
        ebook_id=request.form.get('ebook_id'),
        file_md5=request.form.get('file_md5'),
        fmt=request.form.get('format')
    )
    return res.task_id


@views.route('/result/<int:task_id>')
def show_result(task_id):
    retval = store_ebook.AsyncResult(task_id).get(timeout=1.0)
    return repr(retval)


def check_auth(auth_key):
    # authenticate user
    key_parts = base64.b64decode(str(auth_key), '_-').split('+')
    user = User.validate_auth_key(
        username=key_parts[0],
        api_key=key_parts[1]
    )
    if user is None:
        raise Forbidden
    return user
