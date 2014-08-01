import base64
import codecs
import datetime
import fileinput
import fnmatch
import json
import os

from flask import g, current_app as app

from flask import request, redirect, session, abort, Blueprint
from flask import url_for, render_template, render_template_string, jsonify, make_response
from flask.ext.login import login_required, login_user, logout_user

from werkzeug.exceptions import Forbidden

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
        # display docs listing
        pages = []

        # TODO some kind of caching

        # iterate all the docs
        files = sorted(os.listdir('ogreserver/docs'))
        for filename in fnmatch.filter(files, '*.md'):
            summary = None
            title = None

            # extract the title/summary from the markdown header
            finput = fileinput.input(os.path.join('ogreserver/docs', filename))
            for line in finput:
                if line == '\n':
                    # end of markdown header
                    break
                elif line.startswith('Title'):
                    title = line[7:]
                elif line.startswith('Summary'):
                    summary = line[9:]
            finput.close()

            pages.append({
                'title': title,
                'summary': summary,
                'filename': os.path.splitext(filename)[0],
            })

        return render_template('docs.html', pages=pages)

    else:
        # render a single doc page
        if not os.path.exists('ogreserver/docs/{}.md'.format(doco)):
            abort(404)

        content = []
        in_header = True
        title = None

        # read in a markdown file from the docs
        for line in fileinput.input('ogreserver/docs/{}.md'.format(doco)):
            if in_header:
                # extract title from header
                if line.startswith('Title'):
                    title = line[7:]
                elif line == '\n':
                    in_header = False
            elif in_header is False:
                content.append(line)

        # add a link to edit/improve this page
        improve_url = IMPROVE_URL.format(doco)

        # render a string for the Flask jinja template engine
        return render_template_string('{}{}=\n\n{}{}{}'.format(
            TEMPLATE_MD_START,
            title,
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
    ds = DataStore(app.config, app.logger, app.whoosh)
    s = request.args.get('s')
    if s:
        rs = ds.search(s)
    else:
        rs = ds.search()
    return render_template('list.html', ebooks=rs)


@views.route('/ajax/rating/<pk>')
@login_required
def get_rating(pk):
    ds = DataStore(app.config, app.logger)
    rating = ds.get_rating(pk)
    return jsonify({'rating': rating})


@views.route('/ajax/comment-count/<pk>')
@login_required
def get_comment_count(pk):
    ds = DataStore(app.config, app.logger)
    comments = ds.get_comments(pk)
    return jsonify({'comments': len(comments)})


@views.route('/download/<pk>/', defaults={'fmt': None})
@views.route('/download/<pk>/<fmt>')
@login_required
def download(pk, fmt=None):
    ds = DataStore(app.config, app.logger)
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
    data = json.loads(request.data)

    # stats log the upload
    Log.create(user.id, 'CONNECT', len(data.keys()), user.session_api_key)

    # update the library
    ds = DataStore(app.config, app.logger, app.whoosh)
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
    incoming = [item['file_hash'] for item in data.values()]

    # query books missing from S3 and supply back to the client
    missing_books = ds.get_missing_books(username=user.username, hash_filter=incoming)
    return json.dumps({
        'ebooks_to_update': update_books,
        'ebooks_to_upload': missing_books,
        'messages': msgs
    })


@views.route('/post-logs/<auth_key>', methods=['POST'])
def post_logs(auth_key):
    user = check_auth(auth_key)

    log_file_path = os.path.join(
        app.uploaded_logs.config.destination,
        '{}.{}.log'.format(user.username, datetime.datetime.now().strftime("%Y%m%d-%H%M%S")),
    )

    # ensure target upload directory exists
    if not os.path.exists(os.path.dirname(log_file_path)):
        os.mkdir(os.path.dirname(log_file_path))

    # write request body to file
    with codecs.open(log_file_path, 'w', 'utf-8') as f:
        f.write(u'{}\n'.format(request.data.decode('utf-8')))

    return 'ok'


@views.route('/upload-errord/<auth_key>/<filename>', methods=['POST'])
def upload_errord(auth_key, filename):
    user = check_auth(auth_key)

    filename = u'{}.{}.{}'.format(
        user.username,
        datetime.datetime.now().strftime("%Y%m%d-%H%M%S"),
        filename,
    )

    app.uploaded_logs.save(request.files['ebook'], name=filename)
    return 'ok'


@views.route('/confirm/<auth_key>', methods=['POST'])
def confirm(auth_key):
    check_auth(auth_key)

    # update a file's md5 hash
    current_file_hash = request.form.get('file_hash')
    updated_file_hash = request.form.get('new_hash')

    ds = DataStore(app.config, app.logger)
    if ds.update_book_hash(current_file_hash, updated_file_hash):
        return 'ok'
    else:
        return 'fail'


@views.route('/upload/<auth_key>', methods=['POST'])
def upload(auth_key):
    user = check_auth(auth_key)

    # stats log the upload
    Log.create(user.id, 'UPLOADED', 1, user.session_api_key)

    app.logger.debug('{} {} {}'.format(
        user.session_api_key,
        request.form.get('pk'),
        request.files['ebook'].content_length
    ))

    # write uploaded ebook to disk, named as the hash and filetype
    app.uploaded_ebooks.save(request.files['ebook'], name='{}.{}'.format(
        request.form.get('file_hash'), request.form.get('format')
    ))

    # let celery process the upload
    res = store_ebook.delay(
        user_id=user.id,
        ebook_id=request.form.get('ebook_id'),
        file_hash=request.form.get('file_hash'),
        fmt=request.form.get('format')
    )
    return res.task_id


@views.route('/result/<int:task_id>')
def show_result(task_id):
    retval = store_ebook.AsyncResult(task_id).get(timeout=1.0)
    return repr(retval)


def check_auth(auth_key):
    user = None
    try:
        # authenticate user
        key_parts = base64.b64decode(str(auth_key), '_-').split('+')
        user = User.validate_auth_key(
            username=key_parts[0],
            api_key=key_parts[1]
        )
    except:
        app.logger.error('Bad authentiation key: {}'.format(auth_key), exc_info=True)

    if user is None:
        raise Forbidden
    return user
