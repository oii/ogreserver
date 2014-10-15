from __future__ import absolute_import

import os
import subprocess

import mock
import pytest

from ogreclient.ebook_obj import EbookObject


@pytest.fixture(scope='session')
def calibre_ebook_meta_bin():
    return subprocess.check_output('which ebook-meta', shell=True).strip()


@pytest.fixture(scope='session')
def client_config():
    return {
        'config_dir': None,
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


@pytest.fixture(scope='function')
def parse_author_method():
    return EbookObject._parse_author


@pytest.fixture(scope='function')
def helper_get_ebook(client_config, ebook_lib_path):
    def _get_ebook(filename, basepath=None):
        # ebook_obj creation helper
        ebook_obj = EbookObject(
            config=client_config,
            filepath=os.path.join(basepath, filename) if basepath else os.path.join(ebook_lib_path, filename),
        )
        ebook_obj.get_metadata()
        return ebook_obj

    return _get_ebook


@pytest.yield_fixture(scope='function')
def mock_urlopen():
    m = mock.patch('ogreclient.core.urllib2.urlopen')
    yield m.start()
    m.stop()


@pytest.yield_fixture(scope='function')
def mock_subprocess_popen():
    m = mock.patch('ogreclient.ebook_obj.subprocess.Popen')
    yield m.start()
    m.stop()


@pytest.yield_fixture(scope='function')
def mock_os_environ_get():
    m = mock.patch('ogreclient.prereqs.os.environ.get')
    yield m.start()
    m.stop()


@pytest.yield_fixture(scope='function')
def mock_subprocess_check_output():
    m = mock.patch('ogreclient.prereqs.subprocess.check_output')
    yield m.start()
    m.stop()


@pytest.yield_fixture(scope='function')
def mock_raw_input():
    m = mock.patch('__builtin__.raw_input')
    yield m.start()
    m.stop()


@pytest.yield_fixture(scope='function')
def mock_getpass_getpass():
    m = mock.patch('ogreclient.prereqs.getpass.getpass')
    yield m.start()
    m.stop()


@pytest.yield_fixture(scope='function')
def mock_os_mkdir():
    m = mock.patch('ogreclient.prereqs.os.mkdir')
    yield m.start()
    m.stop()
