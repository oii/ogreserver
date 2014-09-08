from __future__ import absolute_import

from ..models.datastore import DataStore


def test_update_book_hash(flask_app, rethinkdb, user):
    ebooks_dict = {
        u"H. C.\u0006Andersen\u0007Andersen's Fairy Tales": {
            'format': 'epub',
            'file_hash': '38b3fc3a',
            'owner': 'mafro',
            'size': 139654,
            'dedrm': False,
        },
    }

    # create the datastore and run a sync
    ds = DataStore(flask_app.config, flask_app.logger)
    ds.update_library(ebooks_dict, user)

    # check the object in formats table
    format_obj = rethinkdb.db('test').table('formats').get('38b3fc3a').run()
    assert format_obj is not None, 'format should exist with MD5 of 38b3fc3a'

    # md5 is different after ogre_id written to metadata on client
    ret = ds.update_book_hash('38b3fc3a', 'egg')
    assert ret is True, 'update_book_hash() returned false'

    format_obj = rethinkdb.db('test').table('formats').get('egg').run()
    assert format_obj is not None, 'format should have been updated to MD5 of egg'


def test_find_formats(flask_app, user, rethinkdb):
    ds = DataStore(flask_app.config, flask_app.logger)

    # create test ebook data directly in rethinkdb
    rethinkdb.table('ebooks').insert({
        'firstname': 'H. C.',
        'lastname': 'Andersen',
        'title': "Andersen's Fairy Tales",
        'ebook_id': 'bcddb7988cf91f7025dd778ca49ecf9f'
    }).run()
    ds._create_new_version('bcddb7988cf91f7025dd778ca49ecf9f', user.username, {
        'format': 'epub',
        'file_hash': '38b3fc3a',
        'size': 1234,
        'dedrm': False,
    })

    versions = ds.find_formats_by_version('mobi')
    assert len(versions) == 1


def test_find_formats_none(flask_app, user, rethinkdb):
    ds = DataStore(flask_app.config, flask_app.logger)

    # create test ebook data directly in rethinkdb
    rethinkdb.table('ebooks').insert({
        'firstname': 'H. C.',
        'lastname': 'Andersen',
        'title': "Andersen's Fairy Tales",
        'ebook_id': 'bcddb7988cf91f7025dd778ca49ecf9f'
    }).run()
    version_id = ds._create_new_version('bcddb7988cf91f7025dd778ca49ecf9f', user.username, {
        'format': 'epub',
        'file_hash': '38b3fc3a',
        'size': 1234,
        'dedrm': False,
    })
    ds._create_new_format(version_id, '9da4f3ba', 'mobi')

    versions = ds.find_formats_by_version('epub')
    assert len(versions) == 0
    versions = ds.find_formats_by_version('mobi')
    assert len(versions) == 0
