from __future__ import absolute_import
from __future__ import unicode_literals

import collections
import json
from StringIO import StringIO

import mock


def test_get_definitions_list_of_lists(flask_app, ogreclient_auth_token):
    '''
    Ensure /definitions returns a list of lists (which is parsed by ogreclient)
    '''
    client = flask_app.test_client()
    result = client.get('/api/v1/definitions', headers={'Ogre-key': ogreclient_auth_token})
    assert result.status_code == 200

    # ensure list of lists is returned
    assert type(json.loads(result.data)) is list
    assert type(json.loads(result.data)[0]) is list
    assert type(json.loads(result.data)[1]) is list
    assert type(json.loads(result.data)[2]) is list
    assert type(json.loads(result.data)[3]) is list


def test_get_definitions_order(flask_app, ogreclient_auth_token):
    '''
    Test parsing of /definitions data
    '''
    client = flask_app.test_client()
    result = client.get('/api/v1/definitions', headers={'Ogre-key': ogreclient_auth_token})
    assert result.status_code == 200

    # convert list of lists result into OrderedDict
    defs = collections.OrderedDict(
        [(v[0], (v[1],)) for v in json.loads(result.data)]
    )

    # ensure the formats come back in the correct order
    assert defs.keys() == ['mobi', 'pdf', 'azw3', 'epub']
    assert [k for k,v in defs.iteritems() if v[0] is True] == ['mobi', 'azw3', 'epub']


@mock.patch('ogreserver.views.api.open')
def test_download_dedrm(mock_views_api_open, flask_app, ogreclient_auth_token):
    '''
    Test GET to /download-dedrm returns binary data
    '''
    client = flask_app.test_client()
    resp = client.get('/api/v1/download-dedrm', headers={'Ogre-key': ogreclient_auth_token})
    assert resp.status_code == 302


@mock.patch('ogreserver.views.api.ebook_store')
def test_confirm(mock_views_api_ebook_store, flask_app, ogreclient_auth_token):
    '''
    Test POST to /confirm endpoint
    '''
    mock_views_api_ebook_store.update_ebook_hash.return_value = True

    client = flask_app.test_client()
    resp = client.post(
        '/api/v1/confirm',
        headers={'Ogre-key': ogreclient_auth_token},
        data=json.dumps({
            'file_hash': '38b3fc3a',
            'new_hash': 'bcddb798',
        }),
        content_type='application/json'
    )
    assert resp.status_code == 200
    assert mock_views_api_ebook_store.update_ebook_hash.call_count == 1
    assert json.loads(resp.data)['result'] == 'ok'


@mock.patch('ogreserver.views.api.ebook_store')
def test_to_upload(mock_views_api_ebook_store, flask_app, ogreclient_auth_token):
    '''
    Test retrieve uploads from to /to-upload
    '''
    mock_views_api_ebook_store.get_missing_books.return_value = ['fake-book-to-upload.epub']

    client = flask_app.test_client()
    resp = client.get(
        '/api/v1/to-upload',
        headers={'Ogre-key': ogreclient_auth_token}
    )
    assert resp.status_code == 200
    assert mock_views_api_ebook_store.get_missing_books.call_count == 1
    assert json.loads(resp.data)['result'] == ['fake-book-to-upload.epub']


def test_upload(flask_app, ogreclient_auth_token):
    '''
    Test multipart upload to /upload
    '''
    client = flask_app.test_client()
    resp = client.post(
        '/api/v1/upload',
        content_type='multipart/form-data',
        headers={'Ogre-key': ogreclient_auth_token},
        data={
            'ebook_id': 'bcddb798',
            'file_hash': '38b3fc3a',
            'format': 'epub',
            'ebook': (StringIO(str('binary content')), 'legit.epub'),
        }
    )
    assert resp.status_code == 200
    assert json.loads(resp.data)['result'] == 'ok'

    # ensure store signal called
    assert flask_app.signals['upload-ebook'].send.call_count == 1
