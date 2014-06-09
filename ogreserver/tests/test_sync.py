from __future__ import absolute_import

from ..models.datastore import DataStore


def test_sync_duplicate(flask_app, datastore, user):
    ebooks_dict = {
        "H. C. Andersen - Andersen's Fairy Tales": {
            'format': 'epub',
            'author': 'H. C. Andersen',
            'file_md5': '38b3fc3aa7fe67e76f0d8b248e62b940',
            'ogre_id': None,
            'title': "Andersen's Fairy Tales",
            'owner': 'mafro',
            'size': 139654
        }
    }

    # create the datastore and run a sync
    ds = DataStore(flask_app.config, flask_app.logger)
    syncd_books = ds.update_library(ebooks_dict, user)

    # check book needs updating
    key, data = syncd_books.items()[0]
    assert data['update'] is True, "book should've been flagged as needing update"

    # sync again
    syncd_books = ds.update_library(ebooks_dict, user)

    # assert book is duplicate
    key, data = syncd_books.items()[0]
    assert data['dupe'] is True, 'book should be flagged as duplicate'
