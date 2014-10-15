from __future__ import absolute_import

import platform

from collections import namedtuple

from ogreclient.prereqs import setup_ogreclient, setup_user_auth, setup_ebook_home
from ogreclient.printer import DummyPrinter


def test_setup_ogreclient(tmpdir, mock_os_environ_get, mock_subprocess_check_output):
    # setup mock for os.environ.get('XDG_CONFIG_HOME')
    def os_environ_get_side_effect(env_var, default=None):
        if env_var in 'XDG_CONFIG_HOME':
            return tmpdir.strpath
        else:
            return default
    mock_os_environ_get.side_effect = os_environ_get_side_effect

    # setup mock for subprocess.check_output()
    mock_subprocess_check_output.return_value = 'fake-bin-path'

    # setup fake argparse object
    fakeargs = namedtuple(
        'fakeargs',
        ('mode', 'no_drm', 'host', 'ebook_home', 'username', 'password', 'ignore_kindle'),
    )

    config = setup_ogreclient(
        fakeargs('sync', True, 'test', 'param_home', 'param_user', 'param_pass', True),
        DummyPrinter()
    )

    # ensure user params came back from setup_user_auth()
    assert config['ebook_home'] == 'param_home'
    assert config['username'] == 'param_user'
    assert config['password'] == 'param_pass'


def test_setup_user_auth_env(mock_os_environ_get, client_config):
    # setup mock for os.environ.get()
    def os_environ_get_side_effect(env_var, default=None):
        if env_var == 'EBOOK_USER':
            return 'env_user'
        elif env_var == 'EBOOK_PASS':
            return 'env_pass'
        else:
            return default
    mock_os_environ_get.side_effect = os_environ_get_side_effect

    # setup fake argparse object
    fakeargs = namedtuple('fakeargs', ('username', 'password'))

    # setup_user_auth() modifies client_config in place
    setup_user_auth(DummyPrinter(), fakeargs(None, None), client_config)

    # ensure ENV vars are returned when --params are None
    assert client_config['username'] == 'env_user'
    assert client_config['password'] == 'env_pass'


def test_setup_user_auth_config(mock_os_environ_get, client_config):
    # setup mock for os.environ.get()
    mock_os_environ_get.return_value = None

    client_config['username'] = 'client_user'
    client_config['password'] = 'client_pass'

    # setup fake argparse object
    fakeargs = namedtuple('fakeargs', ('username', 'password'))

    # setup_user_auth() modifies client_config in place
    setup_user_auth(DummyPrinter(), fakeargs(None, None), client_config)

    # ensure saved config var returned when ENV & --params are None
    assert client_config['username'] == 'client_user'
    assert client_config['password'] == 'client_pass'


def test_setup_user_auth_params(mock_os_environ_get, mock_raw_input, mock_getpass_getpass, client_config):
    # setup mock for os.environ.get()
    mock_os_environ_get.return_value = None

    # ensure client config vars are ignored
    client_config['username'] = None
    client_config['password'] = None

    # setup mock for raw_input()
    mock_raw_input.return_value = 'manual_user'

    # setup mock for getpass module 
    mock_getpass_getpass.return_value = 'manual_pass'

    # setup fake argparse object
    fakeargs = namedtuple('fakeargs', ('username', 'password'))

    # setup_user_auth() modifies client_config in place
    setup_user_auth(DummyPrinter(), fakeargs(None, None), client_config)

    # ensure ENV vars are returned when --params passed as None
    assert client_config['username'] == 'manual_user'
    assert client_config['password'] == 'manual_pass'


def test_setup_ebook_home_env(mock_os_environ_get, mock_os_mkdir, client_config):
    # setup mock for os.environ.get()
    def os_environ_get_side_effect(env_var, default=None):
        if env_var in 'EBOOK_HOME':
            return 'env_home'
        else:
            return default
    mock_os_environ_get.side_effect = os_environ_get_side_effect

    # setup fake argparse object
    fakeargs = namedtuple('fakeargs', ('ebook_home'))

    _, ebook_home = setup_ebook_home(DummyPrinter(), fakeargs(None), client_config)

    # ensure ENV vars are returned when --params are None
    assert ebook_home == 'env_home'
    assert not mock_os_mkdir.called


def test_setup_ebook_home_params(mock_os_environ_get, mock_os_mkdir, client_config):
    # setup mock for os.environ.get()
    mock_os_environ_get.return_value = None

    client_config['ebook_home'] = 'client_home'

    # setup fake argparse object
    fakeargs = namedtuple('fakeargs', ('ebook_home'))

    _, ebook_home = setup_ebook_home(DummyPrinter(), fakeargs(None), client_config)

    # ensure saved config var returned when ENV & --params are None
    assert ebook_home == 'client_home'
    assert not mock_os_mkdir.called


def test_setup_ebook_home_mkdir(mock_os_environ_get, mock_os_mkdir, client_config):
    # setup mock for os.environ.get()
    mock_os_environ_get.return_value = None

    # no ebook_home supplied
    client_config['ebook_home'] = None
    client_config['platform'] = platform.system()

    # setup fake argparse object
    fakeargs = namedtuple('fakeargs', ('ebook_home'))

    _, ebook_home = setup_ebook_home(DummyPrinter(), fakeargs(None), client_config)

    # ensure mkdir called when no ebook_home specified
    assert mock_os_mkdir.called
