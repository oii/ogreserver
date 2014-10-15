from __future__ import absolute_import

import subprocess

import mock
import pytest


@pytest.fixture(scope='session')
def calibre_ebook_meta_bin():
    return subprocess.check_output('which ebook-meta', shell=True).strip()


@pytest.fixture(scope='session')
def client_config():
    return {
        'config_dir': None,
        'ebook_cache': None,
        'calibre_ebook_meta_bin': '/usr/bin/ebook-meta',
        'providers': {},
        'ebook_home': None,
        'username': 'test',
        'password': 'test',
        'host': 'localhost:6543',
        'verbose': False,
        'quiet': True,
        'no_drm': True,
        'debug': False,
    }


@pytest.yield_fixture(scope='function')
def mock_urlopen(request):
    m = mock.patch('ogreclient.core.urllib2.urlopen')
    yield m.start()
    m.stop()


@pytest.yield_fixture(scope='function')
def mock_subprocess_popen(request):
    m = mock.patch('ogreclient.core.subprocess.Popen')
    yield m.start()
    m.stop()


@pytest.yield_fixture(scope='function')
def mock_os_environ_get(request):
    m = mock.patch('ogreclient.prereqs.os.environ.get')
    yield m.start()
    m.stop()


@pytest.yield_fixture(scope='function')
def mock_subprocess_check_output(request):
    m = mock.patch('ogreclient.prereqs.subprocess.check_output')
    yield m.start()
    m.stop()


@pytest.yield_fixture(scope='function')
def mock_raw_input(request):
    m = mock.patch('__builtin__.raw_input')
    yield m.start()
    m.stop()


@pytest.yield_fixture(scope='function')
def mock_getpass_getpass(request):
    m = mock.patch('ogreclient.prereqs.getpass.getpass')
    yield m.start()
    m.stop()


@pytest.yield_fixture(scope='function')
def mock_os_mkdir():
    m = mock.patch('ogreclient.prereqs.os.mkdir')
    yield m.start()
    m.stop()
