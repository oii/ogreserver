from __future__ import absolute_import
from __future__ import unicode_literals


def test_update_book_hash(datastore, rethinkdb, user):
    # create test ebook data directly in rethinkdb
    rethinkdb.table('ebooks').insert({
        'firstname': 'H. C.',
        'lastname': 'Andersen',
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
    ret = datastore.update_book_hash('38b3fc3a', 'egg')
    assert ret is True, 'update_book_hash() returned false'

    format_obj = rethinkdb.table('formats').get('egg').run()
    assert format_obj is not None, 'format should have been updated to MD5 of egg'


def test_find_formats(datastore, user, rethinkdb):
    '''
    Ensure mobi format is found to be missing from a book with only epub format
    '''
    # create test ebook data directly in rethinkdb
    rethinkdb.table('ebooks').insert({
        'firstname': 'H. C.',
        'lastname': 'Andersen',
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
        'firstname': 'H. C.',
        'lastname': 'Andersen',
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
