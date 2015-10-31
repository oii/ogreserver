from __future__ import absolute_import
from __future__ import unicode_literals

import contextlib
import os

from collections import namedtuple

import mock
import pytest

from ..ogreclient.core import search_for_ebooks as func_search_for_ebooks
from ..ogreclient.ebook_obj import EbookObject
from ..ogreclient.prereqs import setup_user_auth as func_setup_user_auth
from ..ogreclient.prereqs import setup_ebook_home as func_setup_ebook_home
from ..ogreclient.printer import DummyPrinter


@pytest.fixture(scope='function')
def parse_author_method():
    return EbookObject._parse_author


@pytest.fixture(scope='function')
def helper_get_ebook(client_config, ebook_lib_path):
    def wrapped(filename, basepath=None):
        # ebook_obj creation helper
        ebook_obj = EbookObject(
            config=client_config,
            filepath=os.path.join(basepath, filename) if basepath else os.path.join(ebook_lib_path, filename),
            source='TEST'
        )
        ebook_obj.get_metadata()
        return ebook_obj

    return wrapped


@pytest.yield_fixture(scope='function')
def mock_urlopen():
    m = mock.patch('ogre.ogreclient.ogreclient.core.urllib2.urlopen')
    yield m.start()
    m.stop()


@pytest.yield_fixture(scope='function')
def mock_subprocess_popen(calibre_ebook_meta_bin):
    m = mock.patch('ogre.ogreclient.ogreclient.ebook_obj.subprocess.Popen')
    yield m.start()
    m.stop()


@pytest.yield_fixture(scope='function')
def mock_os_environ_get():
    m = mock.patch('ogre.ogreclient.ogreclient.prereqs.os.environ.get')
    yield m.start()
    m.stop()


@pytest.yield_fixture(scope='function')
def mock_subprocess_check_output():
    m = mock.patch('ogre.ogreclient.ogreclient.prereqs.subprocess.check_output')
    yield m.start()
    m.stop()


@pytest.yield_fixture(scope='function')
def mock_raw_input():
    m = mock.patch('__builtin__.raw_input')
    yield m.start()
    m.stop()


@pytest.yield_fixture(scope='function')
def mock_getpass_getpass():
    m = mock.patch('ogre.ogreclient.ogreclient.prereqs.getpass.getpass')
    yield m.start()
    m.stop()


@pytest.yield_fixture(scope='function')
def mock_os_mkdir():
    m = mock.patch('ogre.ogreclient.ogreclient.prereqs.os.mkdir')
    yield m.start()
    m.stop()


@pytest.fixture(scope='session')
def search_for_ebooks():
    def wrapped(client_config):
        data, _, errord = func_search_for_ebooks(client_config, prntr=DummyPrinter())
        return data, errord
    return wrapped


@pytest.fixture(scope='session')
def setup_user_auth():
    def wrapped(client_config):
        # setup fake argparse object
        fakeargs = namedtuple('fakeargs', ('username', 'password'))
        return func_setup_user_auth(
            DummyPrinter(),
            fakeargs(None, None),
            client_config
        )
    return wrapped


@pytest.fixture(scope='session')
def setup_ebook_home():
    def wrapped(client_config):
        # setup fake argparse object
        fakeargs = namedtuple('fakeargs', ('ebook_home'))
        _, ebook_home = func_setup_ebook_home(
            DummyPrinter(),
            fakeargs(None),
            client_config
        )
        return ebook_home
    return wrapped


@pytest.fixture(scope='session')
def cd():
    @contextlib.contextmanager
    def inner_cd(new_path):
        """ Context manager for changing the current working directory """
        saved_path = os.getcwd()
        try:
            os.chdir(new_path)
            yield new_path
        finally:
            os.chdir(saved_path)
    return inner_cd
