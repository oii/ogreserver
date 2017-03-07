from __future__ import absolute_import
from __future__ import unicode_literals

import collections
import json

from StringIO import StringIO


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


def test_download_dedrm_tools_endpoint(flask_app, ogreclient_auth_token, mock_views_api_open):
    '''
    Test GET to /download-dedrm returns binary data
    '''
    client = flask_app.test_client()
    resp = client.get('/api/v1/download-dedrm', headers={'Ogre-key': ogreclient_auth_token})
    assert resp.status_code == 302


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
