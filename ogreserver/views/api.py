from __future__ import absolute_import
from __future__ import unicode_literals

import base64
import codecs
import datetime
import json
import os

from flask import current_app as app
from flask import Blueprint, request, make_response

from werkzeug.exceptions import Forbidden

from ..exceptions import SameHashSuppliedOnUpdateError
from ..models.datastore import DataStore
from ..models.reputation import Reputation
from ..models.user import User

from ..tasks import store_ebook as task_store_ebook

bp_api = Blueprint('api', __name__)


def check_auth(auth_key):
    user = None
    try:
        # authenticate user from supplied API key
        key_parts = base64.b64decode(str(auth_key), '_-').split('+')
        user = User.validate_auth_key(
            username=key_parts[0],
            api_key=key_parts[1]
        )
    except:
        app.logger.error('Bad authentication key: {}'.format(auth_key), exc_info=True)

    if user is None:
        raise Forbidden
    return user


@bp_api.route('/download-dedrm/<auth_key>')
def download_dedrm(auth_key):
    check_auth(auth_key)

    # supply the latest DRM tools to the client
    with open('/var/pypiserver-cache/dedrm-6.0.7.tar.gz', 'r') as f:
        return make_response(f.read())


@bp_api.route('/post/<auth_key>', methods=['POST'])
def post(auth_key):
    user = check_auth(auth_key)

    # get the json payload
    data = json.loads(request.data)

    # stats log the upload
    app.logger.info('CONNECT {}'.format(len(data)))

    # update the library
    ds = DataStore(app.config, app.logger, app.whoosh)
    syncd_books = ds.update_library(data, user)

    # extract the subset of newly supplied books
    new_books = [item for key, item in syncd_books.items() if item['new'] is True]

    # extract the subset of books with missing ogre_id
    update_books = {
        key: item for key, item in syncd_books.items() if item['update'] is True
    }

    app.logger.info('NEW {}'.format(len(new_books)))

    # store sync events
    ds.log_event(user, len(data), len(new_books))

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


@bp_api.route('/post-logs/<auth_key>', methods=['POST'])
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
        f.write('{}\n'.format(request.data.decode('utf-8')))

    return 'ok'


@bp_api.route('/upload-errord/<auth_key>/<filename>', methods=['POST'])
def upload_errord(auth_key, filename):
    user = check_auth(auth_key)

    filename = '{}.{}.{}'.format(
        user.username,
        datetime.datetime.now().strftime("%Y%m%d-%H%M%S"),
        filename,
    )

    app.uploaded_logs.save(request.files['ebook'], name=filename)
    return 'ok'


@bp_api.route('/confirm/<auth_key>', methods=['POST'])
def confirm(auth_key):
    check_auth(auth_key)

    # update a file's md5 hash
    current_file_hash = request.form.get('file_hash')
    updated_file_hash = request.form.get('new_hash')

    ds = DataStore(app.config, app.logger)

    try:
        if ds.update_book_hash(current_file_hash, updated_file_hash):
            return 'ok'
        else:
            return 'fail'
    except SameHashSuppliedOnUpdateError:
        return 'same'


@bp_api.route('/upload/<auth_key>', methods=['POST'])
def upload(auth_key):
    user = check_auth(auth_key)

    # stats log the upload
    app.logger.info('UPLOADED 1')

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
    res = task_store_ebook.delay(
        ebook_id=request.form.get('ebook_id'),
        file_hash=request.form.get('file_hash'),
        fmt=request.form.get('format')
    )
    return res.task_id
