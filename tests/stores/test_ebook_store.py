from __future__ import absolute_import
from __future__ import unicode_literals

from flask import jsonify

from ogreserver.stores import ebooks as ebook_store


def test_update_ebook_hash(postgresql, user, ebook_db_fixture_azw3):
    # md5 is different after ogre_id written to metadata on client
    ret = ebook_store.update_ebook_hash(
        ebook_db_fixture_azw3.versions[0].original_file_hash, 'egg'
    )
    assert ret is True, 'update_ebook_hash() returned false'
    assert ebook_db_fixture_azw3.versions[0].formats[0].file_hash == 'egg', 'file_hash should have been updated to "egg"'


def test_find_formats_missing(postgresql, user, ebook_db_fixture_azw3, ebook_db_fixture_epub):
    '''
    Ensure formats are found to be missing
    '''
    # assert mobi missing from both ebooks
    data = ebook_store.find_missing_formats('mobi')
    assert len(data) == 2
    assert ebook_db_fixture_azw3.versions[0] in data
    assert ebook_db_fixture_epub.versions[0] in data


def test_find_formats_missing_when_format_added(postgresql, user, ebook_db_fixture_azw3, ebook_db_fixture_epub):
    '''
    Ensure formats are found to be missing when an extra format is added to an existing ebook
    '''
    # add mobi format to the first ebook
    ebook_store.create_format(ebook_db_fixture_azw3.versions[0], '9da4f3ba', 'mobi', user=user)

    # assert only ebook2 missing mobi format
    data = ebook_store.find_missing_formats('mobi')
    assert len(data) == 1
    assert ebook_db_fixture_epub.versions[0] == data[0]


def test_find_formats_non_fiction(postgresql, user, ebook_db_fixture_pdf):
    '''
    Ensure that non-fiction books are ignored by find_missing_formats
    '''
    data = ebook_store.find_missing_formats('mobi')
    assert len(data) == 0


def test_find_formats_none(postgresql, user, ebook_db_fixture_azw3):
    '''
    Ensure no formats missing when azw3 & epub already exist
    '''
    ebook_store.create_format(ebook_db_fixture_azw3.versions[0], '9da4f3ba', 'epub', user=user)

    data = ebook_store.find_missing_formats('azw3')
    assert len(data) == 0
    data = ebook_store.find_missing_formats('epub')
    assert len(data) == 0


def test_get_missing_books_json_serializable(postgresql, user, ebook_db_fixture_azw3):
    # add another format and mark uploaded=True
    ebook_store.create_format(ebook_db_fixture_azw3.versions[0], '9da4f3ba', 'mobi', user=user)
    ebook_store.set_uploaded('9da4f3ba', user, filename='egg.pub')

    # validate result is JSON serializable
    assert jsonify(ebook_store.get_missing_books(user=user))


def test_get_missing_books_returns_file_hashes(postgresql, user, ebook_db_fixture_azw3):
    # assert result looks like a list of file_hashes
    data = ebook_store.get_missing_books()
    assert type(data) is list
    assert len(data) == 1
    assert isinstance(data[0], basestring)
    assert len(data[0]) == 32


def test_get_missing_books_for_user(postgresql, user, ebook_db_fixture_azw3):
    '''
    Ensure correct missing books returned for user
    '''
    # add another format and mark uploaded=True
    ebook_store.create_format(ebook_db_fixture_azw3.versions[0], '9da4f3ba', 'mobi', user=user)
    ebook_store.set_uploaded('9da4f3ba', user, filename='egg.pub')

    # should be a single missing book for user
    assert len(ebook_store.get_missing_books(user=user)) == 1


def test_get_missing_books_for_user_after_upload(postgresql, user, ebook_db_fixture_azw3):
    '''
    Ensure correct missing books returned for user
    '''
    # add another version
    ebook_store.create_version(
        ebook_db_fixture_azw3, user, '9da4f3ba', 'epub', 1234, False
    )

    # should now be two missing books for user
    assert len(ebook_store.get_missing_books(user=user)) == 2

    # mark book uploaded
    ebook_store.set_uploaded('9da4f3ba', user, filename='egg.pub')

    # should be a single missing book for user
    assert len(ebook_store.get_missing_books(user=user)) == 1


def test_get_missing_books_for_another_user(postgresql, user2, ebook_db_fixture_azw3):
    '''
    Ensure correct missing books returned for a different user
    '''
    # assert there are no books for user2
    assert len(ebook_store.get_missing_books(user=user2)) == 0

    # add this user as another owner of the un-uploaded file
    ebook_store.append_owner(
        ebook_db_fixture_azw3.versions[0].original_file_hash, user2
    )

    # should be now a single missing book for user2
    assert len(ebook_store.get_missing_books(user=user2)) == 1


def test_create_ebook(postgresql, user, flask_app, ebook_fixture_azw3):
    '''
    Test create method for new ebook
    Uses raw fixture which hasn't been added to the DB for us
    '''
    # create test ebook data
    ebook = ebook_store.create_ebook(
        "Andersen's Fairy Tales", 'H. C. Andersen', user, ebook_fixture_azw3
    )

    # ensure create signal called
    assert flask_app.signals['ebook-created'].send.call_count == 1

    # validate success
    ebook = ebook_store.load_ebook(ebook.id)
    assert ebook.author == 'H. C. Andersen'
    assert ebook.asin == 'B00KG6MZ2O'
    assert len(ebook.versions) == 1

    # verify only format's file_hash is stored against version for provenance
    assert ebook.versions[0].original_file_hash == ebook.versions[0].formats[0].file_hash
    assert ebook.versions[0].original_file_hash == ebook.versions[0].source_format.file_hash


def test_append_ebook_metadata(postgresql, user, flask_app, ebook_db_fixture_azw3):
    '''
    Test merging metadata dicts into ebook object
    '''
    # create fixture for update
    metadata = {
        'publisher': 'Eggselant Books'
    }
    ebook_store.append_ebook_metadata(ebook_db_fixture_azw3, 'amazon', metadata)

    # retrieve ebook from DB and assert update
    ebook = ebook_store.load_ebook(ebook_db_fixture_azw3.id)
    assert ebook.provider_metadata['amazon']['publisher'] == 'Eggselant Books'

    # ensure updated signal called
    assert flask_app.signals['ebook-updated'].send.call_count == 1
