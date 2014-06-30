from __future__ import absolute_import

import subprocess

import mock
import pytest
import virtualenvapi


@pytest.fixture(scope='session')
def calibre_ebook_meta_bin():
    return subprocess.check_output('which ebook-meta', shell=True).strip()


@pytest.fixture(scope='session')
def client_config():
    return {
        'config_dir': None,
        'ebook_cache_path': None,
        'calibre_ebook_meta_bin': '/usr/bin/ebook-meta',
        'ebook_home': None,
        'username': 'test',
        'password': 'test',
        'host': 'localhost:6543',
        'verbose': False,
        'quiet': True,
        'no_drm': True,
    }


@pytest.yield_fixture(scope='function')
def mock_urlopen(request):
    m = mock.patch('ogreclient.core.urllib2.urlopen')
    yield m.start()
    m.stop()


@pytest.yield_fixture(scope='function')
def virtualenv(tmpdir):
    # create a virtualenv in a tmpdir; pytest will clean up for us
    yield virtualenvapi.manage.VirtualEnvironment(tmpdir)
