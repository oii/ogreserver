from __future__ import absolute_import

import pytest

from werkzeug.exceptions import Forbidden

from ..views.api import check_auth


@pytest.mark.xfail
def test_confirm_endpoint():
    pass


def test_authenticate(flask_app, client_config, tmpdir):
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
