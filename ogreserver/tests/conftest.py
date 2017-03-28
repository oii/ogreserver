from __future__ import absolute_import
from __future__ import unicode_literals

import copy
import os
import pytest
import yaml

import whoosh

from ogreserver.models.search import Search
from ogreserver.stores import ebooks as ebook_store

import fixtures


@pytest.yield_fixture(scope='function')
def search(flask_app):
    search = Search(flask_app.whoosh, pagelen=100)
    yield search
    with flask_app.whoosh.writer() as writer:
        writer.mergetype = whoosh.writing.CLEAR


@pytest.fixture(scope='session')
def get_data_fixtures():
    """
    Load a set data fixtures for a particular test. Fixtures must be stored in:
        <test_filename>_fixtures/<testname>.yaml

    This YAML file should contain all fixtures for the test.
    """
    def wrapped(file_path, test_name):
        fixture_path = os.path.join(
            '{}_fixtures'.format(file_path[:-3]),
            '{}.yaml'.format(test_name.split('.')[-1:][0])
        )
        with open(fixture_path, 'r') as f:
            return yaml.load(f.read())
    return wrapped


@pytest.fixture(scope='function')
def ebook_fixture_azw3():
    return copy.deepcopy(fixtures.EBOOK_FIXTURE_1)


@pytest.fixture(scope='function')
def ebook_fixture_pdf():
    return copy.deepcopy(fixtures.EBOOK_FIXTURE_2)


@pytest.fixture(scope='function')
def ebook_fixture_epub():
    return copy.deepcopy(fixtures.EBOOK_FIXTURE_3)


@pytest.yield_fixture(scope='function')
def ebook_db_fixture_azw3(postgresql, ebook_fixture_azw3, user):
    ebook = ebook_store.create_ebook(
        "Andersen's Fairy Tales", 'H. C. Andersen', user, ebook_fixture_azw3
    )
    yield ebook
    postgresql.delete(ebook)
    postgresql.commit()


@pytest.yield_fixture(scope='function')
def ebook_db_fixture_pdf(postgresql, ebook_fixture_pdf, user):
    ebook = ebook_store.create_ebook(
        'Eggbert Yolker', 'The Sun is an Egg', user, ebook_fixture_pdf
    )
    yield ebook
    postgresql.delete(ebook)
    postgresql.commit()


@pytest.yield_fixture(scope='function')
def ebook_db_fixture_epub(postgresql, ebook_fixture_epub, user):
    ebook = ebook_store.create_ebook(
        'Foundation', 'Issac Asimov', user, ebook_fixture_epub
    )
    yield ebook
    postgresql.delete(ebook)
    postgresql.commit()


@pytest.fixture(scope='function')
def ebook_sync_fixture_1(ebook_fixture_azw3):
    return {
        "H. C.\u0006Andersen\u0007Andersen's Fairy Tales": ebook_fixture_azw3
    }


@pytest.fixture(scope='function')
def ebook_sync_fixture_2(ebook_fixture_pdf):
    return {
        'Eggbert\u0006Yolker\u0007The Sun is an Egg': ebook_fixture_pdf
    }
