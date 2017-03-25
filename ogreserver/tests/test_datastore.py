from __future__ import absolute_import
from __future__ import unicode_literals

from flask import jsonify


def test_update_ebook_hash(datastore, postgresql, user, ebook_fixture_azw3):
    # create test ebook data
    ebook = datastore.create_ebook(
        "Andersen's Fairy Tales", 'H. C. Andersen', user, ebook_fixture_azw3
    )

    # md5 is different after ogre_id written to metadata on client
    ret = datastore.update_ebook_hash(ebook_fixture_azw3['file_hash'], 'egg')
    assert ret is True, 'update_ebook_hash() returned false'
    assert ebook.versions[0].formats[0].file_hash == 'egg', 'file_hash should have been updated to "egg"'


def test_find_formats(datastore, postgresql, user, ebook_fixture_azw3, ebook_fixture_epub):
    '''
    Ensure formats are found to be missing
    '''
    # create test ebook data
    ebook1 = datastore.create_ebook(
        "Andersen's Fairy Tales", 'H. C. Andersen', user, ebook_fixture_azw3
    )
    # assert mobi format missing from ebook1
    data = datastore.find_missing_formats('mobi')
    assert len(data) == 1
    assert ebook1.versions[0] == data[0]

    # add another test ebook
    ebook2 = datastore.create_ebook(
        'Foundation', 'Issac Asimov', user, ebook_fixture_epub
    )
    # assert mobi missing from both ebooks
    data = datastore.find_missing_formats('mobi')
    assert len(data) == 2
    assert ebook1.versions[0] in data
    assert ebook2.versions[0] in data

    # add mobi format to the first ebook
    datastore.create_format(ebook1.versions[0], '9da4f3ba', 'mobi', user=user)

    # assert only ebook2 missing mobi format
    data = datastore.find_missing_formats('mobi')
    assert len(data) == 1
    assert ebook2.versions[0] == data[0]


def test_find_formats_non_fiction(datastore, postgresql, user, ebook_fixture_pdf):
    '''
    Ensure that non-fiction books are ignored by find_missing_formats
    '''
    # create test ebook data
    datastore.create_ebook(
        'Eggbert Yolker', 'The Sun is an Egg', user, ebook_fixture_pdf
    )
    data = datastore.find_missing_formats('mobi')
    assert len(data) == 0


def test_find_formats_none(datastore, postgresql, user, ebook_fixture_azw3):
    '''
    Ensure no formats missing when azw3 & epub already exist
    '''
    # create test ebook data
    ebook = datastore.create_ebook(
        "Andersen's Fairy Tales", 'H. C. Andersen', user, ebook_fixture_azw3
    )
    datastore.create_format(ebook.versions[0], '9da4f3ba', 'epub', user=user)

    data = datastore.find_missing_formats('azw3')
    assert len(data) == 0
    data = datastore.find_missing_formats('epub')
    assert len(data) == 0


def test_get_missing_books_json_serializable(datastore, postgresql, user, ebook_fixture_azw3):
    # create test ebook data
    ebook = datastore.create_ebook(
        "Andersen's Fairy Tales", 'H. C. Andersen', user, ebook_fixture_azw3
    )

    # add another format and mark uploaded=True
    datastore.create_format(ebook.versions[0], '9da4f3ba', 'mobi', user=user)
    datastore.set_uploaded('9da4f3ba', user, filename='egg.pub')

    # validate result is JSON serializable
    assert jsonify(datastore.get_missing_books(user=user))


def test_get_missing_books_for_user(datastore, postgresql, user, user2, ebook_fixture_azw3, ebook_fixture_pdf):
    # create test ebook data
    ebook = datastore.create_ebook(
        "Andersen's Fairy Tales", 'H. C. Andersen', user, ebook_fixture_azw3
    )

    # add another format and mark uploaded=True
    datastore.create_format(ebook.versions[0], '9da4f3ba', 'mobi', user=user)
    datastore.set_uploaded('9da4f3ba', user, filename='egg.pub')

    # should be a single missing book for user
    assert len(datastore.get_missing_books(user=user)) == 1

    # add another version
    datastore.create_version(
        ebook, user, ebook_fixture_pdf['file_hash'], 'epub', 1234, False
    )

    # should now be two missing books for user
    assert len(datastore.get_missing_books(user=user)) == 2

    # mark book uploaded
    datastore.set_uploaded(ebook_fixture_pdf['file_hash'], user, filename='egg.pub')

    # should be a single missing book for user
    assert len(datastore.get_missing_books(user=user)) == 1

    # assert there are no books for user2
    assert len(datastore.get_missing_books(user=user2)) == 0

    # add this user as another owner of the un-uploaded file
    datastore.append_owner(ebook_fixture_azw3['file_hash'], user2)

    # should be now a single missing book for user2
    assert len(datastore.get_missing_books(user=user2)) == 1


def test_create_ebook(datastore, postgresql, user, flask_app, ebook_fixture_azw3):
    '''
    Test create method for new ebook
    '''
    # create test ebook data
    ebook = datastore.create_ebook(
        "Andersen's Fairy Tales", 'H. C. Andersen', user, ebook_fixture_azw3
    )

    # ensure create signal called
    assert flask_app.signals['ebook-created'].send.call_count == 1

    # validate success
    ebook = datastore.load_ebook(ebook.id)
    assert ebook.author == 'H. C. Andersen'
    assert ebook.asin == 'B00KG6MZ2O'
    assert len(ebook.versions) == 1

    # verify only format's file_hash is stored against version for provenance
    assert ebook.versions[0].original_file_hash == ebook.versions[0].formats[0].file_hash
    assert ebook.versions[0].original_file_hash == ebook.versions[0].source_format.file_hash


def test_append_ebook_metadata(datastore, postgresql, user, flask_app, ebook_fixture_azw3):
    '''
    Test merging metadata dicts into ebook object
    '''
    # create test ebook data
    ebook = datastore.create_ebook(
        "Andersen's Fairy Tales", 'H. C. Andersen', user, ebook_fixture_azw3
    )

    # create fixture for update
    metadata = {
        'publisher': 'Eggselant Books'
    }
    datastore.append_ebook_metadata(ebook, 'amazon', metadata)

    # retrieve ebook from DB and assert update
    ebook = datastore.load_ebook(ebook.id)
    assert ebook.provider_metadata['amazon']['publisher'] == 'Eggselant Books'

    # ensure updated signal called
    assert flask_app.signals['ebook-updated'].send.call_count == 1
