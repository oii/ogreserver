from __future__ import absolute_import
from __future__ import unicode_literals

import pytest

from ogreserver.exceptions import NoFormatAvailableError
from ogreserver.stores import ebooks as ebook_store


def test_get_best_ebook_filehash_specific_format(postgresql, user, ebook_db_fixture_azw3):
    # mark single format as uploaded
    ebook_store.set_uploaded(
        ebook_db_fixture_azw3.versions[0].source_format.file_hash, user, filename='egg.azw3'
    )

    file_hash = ebook_store.get_best_ebook_filehash(
        ebook_db_fixture_azw3.id, version_id=ebook_db_fixture_azw3.versions[0].id, fmt='azw3'
    )

    # assert filehash is from the first version in DB
    assert file_hash == ebook_db_fixture_azw3.versions[0].source_format.file_hash


def test_get_best_ebook_filehash_none_uploaded(postgresql, user, ebook_db_fixture_azw3):
    # assert exception since no formats are marked as 'uploaded'
    with pytest.raises(NoFormatAvailableError):
        ebook_store.get_best_ebook_filehash(
            ebook_db_fixture_azw3.id,
            version_id=ebook_db_fixture_azw3.versions[0].id, fmt='azw3'
        )


def test_get_best_ebook_filehash_user_preferred_format(postgresql, user, ebook_db_fixture_azw3):
    # mark first format as uploaded
    ebook_store.set_uploaded(
        ebook_db_fixture_azw3.versions[0].source_format.file_hash, user, filename='egg.azw3'
    )

    # create another format against the single version
    ebook_store.create_format(ebook_db_fixture_azw3.versions[0], 'f7025dd7', 'mobi', user=user)

    # mark first format as uploaded
    ebook_store.set_uploaded('f7025dd7', user, filename='egg.mobi')

    # test user.preferred_ebook_format == 'mobi'
    file_hash = ebook_store.get_best_ebook_filehash(
        ebook_db_fixture_azw3.id,
        version_id=ebook_db_fixture_azw3.versions[0].id,
        user=user
    )

    # assert filehash is from the first version in DB
    assert file_hash == 'f7025dd7'


def test_get_best_ebook_filehash_OGRE_preferred_format(postgresql, user, ebook_db_fixture_azw3):
    # mark first format as uploaded
    ebook_store.set_uploaded(
        ebook_db_fixture_azw3.versions[0].source_format.file_hash, user, filename='egg.azw3'
    )

    # create another format against the single version
    ebook_store.create_format(ebook_db_fixture_azw3.versions[0], 'f7025dd7', 'mobi', user=user)

    # mark first format as uploaded
    ebook_store.set_uploaded('f7025dd7', user, filename='egg.mobi')

    # test OGRE's EBOOK_FORMATS config supplies 'egg' top
    file_hash = ebook_store.get_best_ebook_filehash(
        ebook_db_fixture_azw3.id,
        version_id=ebook_db_fixture_azw3.versions[0].id,
    )

    # assert filehash is from the first version in DB
    assert file_hash == 'f7025dd7'


def test_get_best_ebook_filehash_uploaded(postgresql, user, ebook_db_fixture_azw3):
    # create another format against the single version
    ebook_store.create_format(ebook_db_fixture_azw3.versions[0], 'f7025dd7', 'egg', user=user)

    # mark first format as uploaded
    ebook_store.set_uploaded('f7025dd7', user, filename='egg.egg')

    # test get file_hash for format where uploaded is True
    file_hash = ebook_store.get_best_ebook_filehash(
        ebook_db_fixture_azw3.id,
        version_id=ebook_db_fixture_azw3.versions[0].id
    )

    # assert filehash is from the first version in DB
    assert file_hash == 'f7025dd7'
