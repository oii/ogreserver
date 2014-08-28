from __future__ import absolute_import

import pytest

from werkzeug.exceptions import Forbidden

from ..models.datastore import DataStore
from ..views.api import check_auth


@pytest.mark.xfail
def test_confirm_endpoint():
    pass


def test_authenticate(flask_app, client_config, tmpdir):
    flask_app.testing = True
    test_app = flask_app.test_client()

    # authenticate with the server, receiving a session key
    response = test_app.post('/auth', data={
        'username': client_config['username'],
        'password': client_config['password'],
    })
    session_key = response.data

    # verify the session key works
    user = check_auth(session_key)
    assert user.username == client_config['username']

    with pytest.raises(Forbidden):
        check_auth('bad_session_key')


def test_update_book_hash(flask_app, datastore, user):
    ebooks_dict = {
        u"H. C.\u0006Andersen\u0007Andersen's Fairy Tales": {
            'format': 'epub',
            'file_hash': '38b3fc3a',
            'owner': 'mafro',
            'size': 139654,
            'dedrm': False,
        },
    }

    # create the datastore and run a sync
    ds = DataStore(flask_app.config, flask_app.logger)
    ds.update_library(ebooks_dict, user)

    # check the object in formats table
    format_obj = datastore.db('test').table('formats').get('38b3fc3a').run()
    assert format_obj is not None, 'format should exist with MD5 of 38b3fc3a'

    # md5 is different after ogre_id written to metadata on client
    ret = ds.update_book_hash('38b3fc3a', 'egg')
    assert ret is True, 'update_book_hash() returned false'

    format_obj = datastore.db('test').table('formats').get('egg').run()
    assert format_obj is not None, 'format should have been updated to MD5 of egg'
