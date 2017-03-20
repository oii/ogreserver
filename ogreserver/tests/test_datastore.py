from __future__ import absolute_import
from __future__ import unicode_literals

import datetime


def test_update_ebook_hash(datastore, rethinkdb, user, ebook_fixture_azw3):
    # create test ebook data
    datastore._create_new_ebook(
        "Andersen's Fairy Tales", 'H. C. Andersen', user, ebook_fixture_azw3
    )

    # md5 is different after ogre_id written to metadata on client
    ret = datastore.update_ebook_hash(ebook_fixture_azw3['file_hash'], 'egg')
    assert ret is True, 'update_ebook_hash() returned false'

    format_obj = rethinkdb.table('formats').get('egg').run()
    assert format_obj is not None, 'format should have been updated to MD5 of egg'


def test_find_formats(datastore, user, rethinkdb, ebook_fixture_azw3):
    '''
    Ensure mobi format is found to be missing from a book with only epub format
    '''
    # create test ebook data
    datastore._create_new_ebook(
        "Andersen's Fairy Tales", 'H. C. Andersen', user, ebook_fixture_azw3
    )
    data = datastore.find_missing_formats('mobi')
    assert len(data) == 1


def test_find_formats_non_fiction(datastore, user, rethinkdb, ebook_fixture_pdf):
    '''
    Ensure that non-fiction books are ignored by find_missing_formats
    '''
    # create test ebook data
    datastore._create_new_ebook(
        'Eggbert Yolker', 'The Sun is an Egg', user, ebook_fixture_pdf
    )
    data = datastore.find_missing_formats('mobi')
    assert len(data) == 0


def test_find_formats_none(datastore, user, rethinkdb, ebook_fixture_azw3):
    '''
    Ensure no formats missing when azw3 & epub already exist
    '''
    # create test ebook data
    ebook_id = datastore._create_new_ebook(
        "Andersen's Fairy Tales", 'H. C. Andersen', user, ebook_fixture_azw3
    )
    ebook_data = datastore.load_ebook(ebook_id)
    datastore._create_new_format(ebook_data['versions'][0]['version_id'], '9da4f3ba', 'epub', user=user)

    data = datastore.find_missing_formats('azw3')
    assert len(data) == 0
    data = datastore.find_missing_formats('epub')
    assert len(data) == 0


def test_get_missing_books_for_user(datastore, user, user2, rethinkdb, ebook_fixture_azw3, ebook_fixture_pdf):
    # create test ebook data
    ebook_id = datastore._create_new_ebook(
        "Andersen's Fairy Tales", 'H. C. Andersen', user, ebook_fixture_azw3
    )
    ebook_data = datastore.load_ebook(ebook_id)

    # add another format and mark uploaded=True
    datastore._create_new_format(ebook_data['versions'][0]['version_id'], '9da4f3ba', 'mobi', user=user)
    datastore.set_uploaded('9da4f3ba', user, filename='egg.pub')

    # should be a single missing book for user
    assert len(datastore.get_missing_books(user=user)) == 1

    # add another version
    datastore._create_new_version(
        ebook_id, user, ebook_fixture_pdf['file_hash'], 'epub', 1234, False
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


def test_create_new_ebook(datastore, rethinkdb, user, flask_app, ebook_fixture_azw3):
    '''
    Test create method for new ebook
    '''
    # create test ebook data
    ebook_id = datastore._create_new_ebook(
        "Andersen's Fairy Tales", 'H. C. Andersen', user, ebook_fixture_azw3
    )

    # ensure create signal called
    assert flask_app.signals['ebook-created'].send.call_count == 1

    # retrieve ebook from DB and verify
    ebook = datastore.load_ebook(ebook_id)
    assert ebook['author'] == 'H. C. Andersen'
    assert ebook['meta']['asin'] == 'B00KG6MZ2O'
    assert len(ebook['versions']) == 1

    # verify only format's file_hash is stored against version for provenance
    assert ebook['versions'][0]['original_filehash'] == ebook['versions'][0]['formats'][0]['file_hash']


def test_append_ebook_metadata(datastore, rethinkdb, user, flask_app, ebook_fixture_azw3):
    '''
    Test merging metadata dicts into ebook object
    '''
    # create test ebook data
    ebook_id = datastore._create_new_ebook(
        "Andersen's Fairy Tales", 'H. C. Andersen', user, ebook_fixture_azw3
    )

    # create fixture for update
    metadata = {
        'amazon': {
            'publication_date': datetime.date(2014, 7, 15)
        }
    }
    datastore.append_ebook_metadata(ebook_id, metadata)

    # retrieve ebook from DB and assert update
    ebook = datastore.load_ebook(ebook_id)
    assert type(ebook['meta']['amazon']['publication_date']) is datetime.datetime

    # ensure updated signal called
    assert flask_app.signals['ebook-updated'].send.call_count == 1
