from __future__ import absolute_import


def test_update_book_hash(datastore, rethinkdb, user):
    # create test ebook data directly in rethinkdb
    rethinkdb.table('ebooks').insert({
        'firstname': 'H. C.',
        'lastname': 'Andersen',
        'title': "Andersen's Fairy Tales",
        'ebook_id': 'bcddb7988cf91f7025dd778ca49ecf9f'
    }).run()
    datastore._create_new_version('bcddb7988cf91f7025dd778ca49ecf9f', user.username, {
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
    # create test ebook data directly in rethinkdb
    rethinkdb.table('ebooks').insert({
        'firstname': 'H. C.',
        'lastname': 'Andersen',
        'title': "Andersen's Fairy Tales",
        'ebook_id': 'bcddb7988cf91f7025dd778ca49ecf9f'
    }).run()
    datastore._create_new_version('bcddb7988cf91f7025dd778ca49ecf9f', user.username, {
        'format': 'epub',
        'file_hash': '38b3fc3a',
        'size': 1234,
        'dedrm': False,
    })

    versions = datastore.find_missing_formats('mobi')
    assert len(versions) == 1


def test_find_formats_none(datastore, user, rethinkdb):
    # create test ebook data directly in rethinkdb
    rethinkdb.table('ebooks').insert({
        'firstname': 'H. C.',
        'lastname': 'Andersen',
        'title': "Andersen's Fairy Tales",
        'ebook_id': 'bcddb7988cf91f7025dd778ca49ecf9f'
    }).run()
    version_id = datastore._create_new_version('bcddb7988cf91f7025dd778ca49ecf9f', user.username, {
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
