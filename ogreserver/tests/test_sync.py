from __future__ import absolute_import

from ..models.datastore import DataStore


def test_sync_duplicate(flask_app, datastore, user):
    ebooks_dict = {
        "H. C. Andersen - Andersen's Fairy Tales": {
            'format': 'epub',
            'file_md5': '38b3fc3aa7fe67e76f0d8b248e62b940',
            'owner': 'mafro',
            'size': 139654
        },
    }

    # create the datastore and run a sync
    ds = DataStore(flask_app.config, flask_app.logger)
    syncd_books = ds.update_library(ebooks_dict, user)

    # assert book is new
    key, data = syncd_books.items()[0]
    assert data['dupe'] is False, 'book should not be a duplicate'

    # sync again
    syncd_books = ds.update_library(ebooks_dict, user)

    # assert book is duplicate
    key, data = syncd_books.items()[0]
    assert data['dupe'] is True, 'book should be a duplicate'


def test_sync_ebook_update(flask_app, datastore, user):
    ebooks_dict = {
        "H. C. Andersen - Andersen's Fairy Tales": {
            'format': 'epub',
            'file_md5': 'b889dec977aef12c6973acc2cf5b8590',
            'owner': 'mafro',
            'size': 139654
        },
    }

    # create the datastore and run a sync
    ds = DataStore(flask_app.config, flask_app.logger)
    syncd_books = ds.update_library(ebooks_dict, user)

    # check book needs updating
    key, data = syncd_books.items()[0]
    assert data['update'] is True, 'book should need update'
    assert 'ebook_id' in data, 'ebook_id should be present in ogreserver response'

    # set ebook_id in incoming data, same as ogreclient would
    ebooks_dict[ebooks_dict.keys()[0]]['ebook_id'] = data['ebook_id']

    # sync again
    syncd_books = ds.update_library(ebooks_dict, user)

    # assert book does not need update
    key, data = syncd_books.items()[0]
    assert data['update'] is False, 'book should not need update'
