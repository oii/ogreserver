from __future__ import absolute_import

import os
import pytest
import subprocess


@pytest.fixture(scope='session')
def calibre_ebook_meta_bin():
    return subprocess.check_output('which ebook-meta', shell=True).strip()


@pytest.fixture(scope='session')
def ebook_lib_path():
    # path where conftest.py resides + '/ebooks'
    return os.path.join(os.path.dirname(__file__), 'ebooks')


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
