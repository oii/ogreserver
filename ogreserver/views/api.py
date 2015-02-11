from __future__ import absolute_import
from __future__ import unicode_literals

import codecs
import datetime
import json
import os

from flask import current_app as app
from flask import Blueprint, request, make_response, jsonify, abort
from flask.ext.security import current_user
from flask.ext.security.decorators import auth_token_required
from flask.ext.uploads import UploadNotAllowed

from ..exceptions import SameHashSuppliedOnUpdateError
from ..models.datastore import DataStore
from ..models.reputation import Reputation

bp_api = Blueprint('api', __name__, url_prefix='/api/v1')


@bp_api.route('/definitions')
@auth_token_required
def get_definitions():
    # return to the current ebook format definitions to the client
    return jsonify(app.config['EBOOK_DEFINITIONS'])


@bp_api.route('/download-dedrm')
@auth_token_required
def download_dedrm():
    # supply the latest DRM tools to the client
    with open('/var/pypiserver-cache/dedrm-6.0.7.tar.gz', 'r') as f:
        return make_response(f.read())


@bp_api.route('/post', methods=['POST'])
@auth_token_required
def post():
    # stats log the upload
    app.logger.info('CONNECT {}'.format(len(request.json)))

    # update the library
    ds = DataStore(app.config, app.logger, app.whoosh)
    syncd_books = ds.update_library(request.json, current_user)

    # extract the subset of newly supplied books
    new_books = [item for key, item in syncd_books.items() if item['new'] is True]

    # extract the subset of books with missing ogre_id
    update_books = {
        key: item for key, item in syncd_books.items() if item['update'] is True
    }

    # extract list of errors
    errors = [item['error'] for key, item in syncd_books.items() if 'error' in item.keys()]

    app.logger.info('NEW {}'.format(len(new_books)))

    # store sync events
    ds.log_event(current_user, len(request.json), len(new_books))

    # handle badge and reputation changes
    r = Reputation(current_user)
    r.new_ebooks(len(new_books))
    r.earn_badges()
    msgs = r.get_new_badges()

    return json.dumps({
        'to_update': update_books,
        'messages': msgs,
        'errors': errors
    })


@bp_api.route('/post-logs', methods=['POST'])
@auth_token_required
def post_logs():
    log_file_path = os.path.join(
        app.uploaded_logs.config.destination,
        '{}.{}.log'.format(
            current_user.username,
            datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        ),
    )

    # ensure target upload directory exists
    if not os.path.exists(os.path.dirname(log_file_path)):
        os.mkdir(os.path.dirname(log_file_path))

    # write request body to file
    with codecs.open(log_file_path, 'w', 'utf-8') as f:
        f.write('{}\n'.format(request.data.decode('utf-8')))

    return 'ok'


@bp_api.route('/upload-errord/<filename>', methods=['POST'])
@auth_token_required
def upload_errord(filename):
    filename = '{}.{}.{}'.format(
        current_user.username,
        datetime.datetime.now().strftime("%Y%m%d-%H%M%S"),
        filename,
    )

    app.uploaded_logs.save(request.files['ebook'], name=filename)
    return 'ok'


@bp_api.route('/confirm', methods=['POST'])
@auth_token_required
def confirm():
    # update a file's md5 hash
    current_file_hash = request.json['file_hash']
    updated_file_hash = request.json['new_hash']

    ds = DataStore(app.config, app.logger)

    try:
        if ds.update_book_hash(current_file_hash, updated_file_hash):
            return 'ok'
        else:
            return 'fail'
    except SameHashSuppliedOnUpdateError:
        return 'same'


@bp_api.route('/to-upload', methods=['GET'])
@auth_token_required
def to_upload():
    ds = DataStore(app.config, app.logger, app.whoosh)

    # query books to upload and supply back to the client
    missing_books = ds.get_missing_books(username=current_user.username)

    return json.dumps(missing_books)


@bp_api.route('/upload', methods=['POST'])
@auth_token_required
def upload():
    # stats log the upload
    app.logger.info('UPLOADED 1')

    app.logger.debug('{} {} {}'.format(
        current_user.username,
        request.form.get('ebook_id'),
        request.files['ebook'].content_length
    ))

    try:
        # write uploaded ebook to disk, named as the hash and filetype
        upload_path = app.uploaded_ebooks.save(
            request.files['ebook'],
            name='{}.{}'.format(
                request.form.get('file_hash'), request.form.get('format')
            )
        )
    except UploadNotAllowed:
        abort(415)

    # signal celery to process the upload
    app.signals['store-ebook'].send(
        bp_api,
        ebook_id=request.form.get('ebook_id'),
        filename=upload_path,
        file_hash=request.form.get('file_hash'),
        fmt=request.form.get('format'),
        username=current_user.username
    )
    return 'ok'
