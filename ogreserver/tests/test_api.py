from __future__ import absolute_import
from __future__ import unicode_literals

import collections
import json

from StringIO import StringIO


def test_login_ok(flask_app, user):
    '''
    Test /login endpoint
    '''
    client = flask_app.test_client()
    result = client.post(
        '/login',
        data=json.dumps({'email': user.email, 'password': user.username}),
        content_type='application/json'
    )
    assert result.status_code == 200
    assert json.loads(result.data)['meta']['code'] == 200
    assert json.loads(result.data)['response']['user']['id'] == '1'
    assert 'authentication_token' in json.loads(result.data)['response']['user']


def test_login_bad_creds(flask_app, user):
    '''
    Test /login with bad credentials
    '''
    client = flask_app.test_client()
    result = client.post(
        '/login',
        data=json.dumps({'email': user.email, 'password': 'eggsbacon'}),
        content_type='application/json'
    )
    assert result.status_code == 200
    assert json.loads(result.data)['meta']['code'] == 400
    assert json.loads(result.data)['response']['errors']['password'][0] == 'Invalid password'


def test_login_without_email_address(flask_app, user):
    '''
    Test /login without an email address
    '''
    client = flask_app.test_client()
    result = client.post(
        '/login',
        data=json.dumps({'password': user.username}),
        content_type='application/json'
    )
    assert result.status_code == 200
    assert json.loads(result.data)['meta']['code'] == 400
    assert json.loads(result.data)['response']['errors']['email'][0] == 'Email not provided'


def test_unauthorized(flask_app):
    '''
    Test an API endpoint without a Ogre-Key headers
    '''
    client = flask_app.test_client()
    result = client.get('/api/v1/definitions')
    assert result.status_code == 401


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
    assert type(json.loads(result.data)[4]) is list


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
    assert defs.keys() == ['mobi', 'pdf', 'azw', 'azw3', 'epub']
    assert [k for k,v in defs.iteritems() if v[0] is True] == ['mobi', 'azw3', 'epub']


def test_download_dedrm_tools_endpoint(flask_app, ogreclient_auth_token, mock_views_api_open):
    '''
    Test GET to /download-dedrm returns binary data
    '''
    client = flask_app.test_client()
    resp = client.get('/api/v1/download-dedrm', headers={'Ogre-key': ogreclient_auth_token})
    assert resp.status_code == 200
    assert resp.data == 'API open() data'


def test_upload_endpoint(flask_app, ogreclient_auth_token):
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
