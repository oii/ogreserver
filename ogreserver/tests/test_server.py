from __future__ import absolute_import
from __future__ import unicode_literals

import base64
import pytest

from werkzeug.exceptions import Forbidden


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

    from ..views.api import check_auth

    # verify the session key works
    user = check_auth(session_key)
    assert user.username == client_config['username']

    with pytest.raises(Forbidden):
        check_auth(base64.b64encode('bad_session+key'))
