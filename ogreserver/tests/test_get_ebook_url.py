from __future__ import absolute_import
from __future__ import unicode_literals

from ogreserver.exceptions import NoFormatAvailableError

import pytest


def test_get_best_ebook_filehash_specific_format(datastore, user, rethinkdb, ebook_fixture_azw3):
    # create test ebook data
    ebook_id = datastore._create_new_ebook(
        "Andersen's Fairy Tales", 'H. C. Andersen', user, ebook_fixture_azw3
    )
    ebook_data = datastore.load_ebook(ebook_id)

    # mark single format as uploaded
    datastore.set_uploaded(ebook_fixture_azw3['file_hash'], user, filename='egg.azw3')

    file_hash = datastore._get_best_ebook_filehash(
        ebook_id, version_id=ebook_data['versions'][0]['version_id'], fmt='azw3'
    )

    # assert filehash is from the first version in rethinkdb
    assert file_hash == ebook_fixture_azw3['file_hash']


def test_get_best_ebook_filehash_none_uploaded(datastore, user, rethinkdb, ebook_fixture_azw3):
    # create test ebook data
    ebook_id = datastore._create_new_ebook(
        "Andersen's Fairy Tales", 'H. C. Andersen', user, ebook_fixture_azw3
    )
    ebook_data = datastore.load_ebook(ebook_id)

    # assert exception since no formats are marked as 'uploaded'
    with pytest.raises(NoFormatAvailableError):
        datastore._get_best_ebook_filehash(
            ebook_id, version_id=ebook_data['versions'][0]['version_id'], fmt='azw3'
        )


def test_get_best_ebook_filehash_user_preferred_format(datastore, user, rethinkdb, ebook_fixture_azw3):
    # create test ebook data
    ebook_id = datastore._create_new_ebook(
        "Andersen's Fairy Tales", 'H. C. Andersen', user, ebook_fixture_azw3
    )
    ebook_data = datastore.load_ebook(ebook_id)

    # mark first format as uploaded
    datastore.set_uploaded(ebook_fixture_azw3['file_hash'], user, filename='egg.azw3')

    # create another format against the single version
    datastore._create_new_format(ebook_data['versions'][0]['version_id'], 'f7025dd7', 'mobi', user=user)

    # mark first format as uploaded
    datastore.set_uploaded('f7025dd7', user, filename='egg.mobi')

    # test user.preferred_ebook_format == 'mobi'
    file_hash = datastore._get_best_ebook_filehash(
        ebook_id,
        version_id=ebook_data['versions'][0]['version_id'],
        user=user
    )

    # assert filehash is from the first version in rethinkdb
    assert file_hash == 'f7025dd7'


def test_get_best_ebook_filehash_OGRE_preferred_format(datastore, user, rethinkdb, ebook_fixture_azw3):
    # create test ebook data
    ebook_id = datastore._create_new_ebook(
        "Andersen's Fairy Tales", 'H. C. Andersen', user, ebook_fixture_azw3
    )
    ebook_data = datastore.load_ebook(ebook_id)

    # mark first format as uploaded
    datastore.set_uploaded(ebook_fixture_azw3['file_hash'], user, filename='egg.azw3')

    # create another format against the single version
    datastore._create_new_format(ebook_data['versions'][0]['version_id'], 'f7025dd7', 'mobi', user=user)

    # mark first format as uploaded
    datastore.set_uploaded('f7025dd7', user, filename='egg.mobi')

    # test OGRE's EBOOK_FORMATS config supplies 'egg' top
    file_hash = datastore._get_best_ebook_filehash(
        ebook_id,
        version_id=ebook_data['versions'][0]['version_id'],
    )

    # assert filehash is from the first version in rethinkdb
    assert file_hash == 'f7025dd7'


def test_get_best_ebook_filehash_uploaded(datastore, user, rethinkdb, ebook_fixture_azw3):
    # create test ebook data
    ebook_id = datastore._create_new_ebook(
        "Andersen's Fairy Tales", 'H. C. Andersen', user, ebook_fixture_azw3
    )
    ebook_data = datastore.load_ebook(ebook_id)

    # create another format against the single version
    datastore._create_new_format(ebook_data['versions'][0]['version_id'], 'f7025dd7', 'egg', user=user)

    # mark first format as uploaded
    datastore.set_uploaded('f7025dd7', user, filename='egg.egg')

    # test get file_hash for format where uploaded is True
    file_hash = datastore._get_best_ebook_filehash(
        ebook_id,
        version_id=ebook_data['versions'][0]['version_id']
    )

    # assert filehash is from the first version in rethinkdb
    assert file_hash == 'f7025dd7'
