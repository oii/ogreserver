from __future__ import absolute_import
from __future__ import unicode_literals

import json


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
