from __future__ import absolute_import
from __future__ import unicode_literals

import datetime


def test_update_ebook_hash(datastore, rethinkdb, user):
    # create test ebook data directly in rethinkdb
    rethinkdb.table('ebooks').insert({
        'author': 'H. C. Andersen',
        'title': "Andersen's Fairy Tales",
        'ebook_id': 'bcddb798'
    }).run()
    datastore._create_new_version('bcddb798', user.username, {
        'format': 'epub',
        'file_hash': '38b3fc3a',
        'size': 1234,
        'dedrm': False,
    })

    # md5 is different after ogre_id written to metadata on client
    ret = datastore.update_ebook_hash('38b3fc3a', 'egg')
    assert ret is True, 'update_ebook_hash() returned false'

    format_obj = rethinkdb.table('formats').get('egg').run()
    assert format_obj is not None, 'format should have been updated to MD5 of egg'


def test_find_formats(datastore, user, rethinkdb):
    '''
    Ensure mobi format is found to be missing from a book with only epub format
    '''
    # create test ebook data directly in rethinkdb
    rethinkdb.table('ebooks').insert({
        'author': 'H. C. Andersen',
        'title': "Andersen's Fairy Tales",
        'ebook_id': 'bcddb798'
    }).run()
    datastore._create_new_version('bcddb798', user.username, {
        'format': 'epub',
        'file_hash': '38b3fc3a',
        'size': 1234,
        'dedrm': False,
    })

    versions = datastore.find_missing_formats('mobi')
    assert len(versions) == 1


def test_find_formats_none(datastore, user, rethinkdb):
    '''
    Ensure no formats missing when both epub & mobi are available
    '''
    # create test ebook data directly in rethinkdb
    rethinkdb.table('ebooks').insert({
        'author': 'H. C. Andersen',
        'title': "Andersen's Fairy Tales",
        'ebook_id': 'bcddb798'
    }).run()
    version_id = datastore._create_new_version('bcddb798', user.username, {
        'format': 'epub',
        'file_hash': '38b3fc3a',
        'size': 1234,
        'dedrm': False,
    })
    datastore._create_new_format(version_id, '9da4f3ba', 'mobi')

    versions = datastore.find_missing_formats('epub')
    assert len(versions) == 0
    versions = datastore.find_missing_formats('mobi')
    assert len(versions) == 0


def test_get_missing_books_for_user(datastore, user, user2, rethinkdb):
    # create test ebook data directly in rethinkdb
    rethinkdb.table('ebooks').insert({
        'author': 'H. C. Andersen',
        'title': "Andersen's Fairy Tales",
        'ebook_id': 'bcddb798'
    }).run()
    version_id = datastore._create_new_version('bcddb798', user.username, {
        'format': 'epub',
        'file_hash': '38b3fc3a',
        'size': 1234,
        'dedrm': False,
    })
    # add another format and mark uploaded=True
    datastore._create_new_format(version_id, '9da4f3ba', 'mobi', username=user.username)
    datastore.set_uploaded('9da4f3ba', user.username, filename='egg.pub')

    # should be a single missing book for user
    assert len(datastore.get_missing_books(username=user.username)) == 1

    # add another version
    version_id = datastore._create_new_version('bcddb798', user.username, {
        'format': 'epub',
        'file_hash': '06bc5351',
        'size': 1234,
        'dedrm': False,
    })

    # should now be two missing books for user
    assert len(datastore.get_missing_books(username=user.username)) == 2

    # mark book uploaded
    datastore.set_uploaded('06bc5351', user.username, filename='egg.pub')

    # should be a single missing book for user
    assert len(datastore.get_missing_books(username=user.username)) == 1

    # assert there are no books for user2
    assert len(datastore.get_missing_books(username=user2.username)) == 0

    # add this user as another owner of the un-uploaded file
    datastore.append_owner('38b3fc3a', user2.username)

    # should be now a single missing book for user2
    assert len(datastore.get_missing_books(username=user2.username)) == 1


def test_update_ebook(datastore, rethinkdb, user):
    '''
    Test conversion of datetime objects into rql objects
    '''
    # create test ebook data directly in rethinkdb
    ebook_data = {
        'author': 'H. C. Andersen',
        'title': "Andersen's Fairy Tales",
        'ebook_id': 'bcddb798',
        'meta': {
            'asin': 'B00KG6MZ2O',
        }
    }
    rethinkdb.table('ebooks').insert(ebook_data).run()

    # create fixture for update
    data = {
        'author': 'eggsbacon',
        'meta': {
            'asin': 'eggsbacon',
            'amazon': {
                'publication_date': datetime.date(2014, 7, 15)
            }
        }
    }
    datastore.update_ebook('bcddb798', data)

    # retrieve ebook from rethinkdb and assert update
    obj = datastore.load_ebook(ebook_data['ebook_id'])
    assert obj['author'] == 'eggsbacon'
    assert obj['meta']['asin'] == 'eggsbacon'
    assert type(obj['meta']['amazon']['publication_date']) is datetime.datetime
