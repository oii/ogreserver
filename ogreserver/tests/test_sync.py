from __future__ import absolute_import
from __future__ import unicode_literals


def test_sync_duplicate(datastore, rethinkdb, user):
    '''
    Test two basic syncs with the same data. Book should be flagged as dupe
    '''
    ebooks_dict = {
        "H. C.\u0006Andersen\u0007Andersen's Fairy Tales": {
            'format': 'epub',
            'file_hash': '38b3fc3a',
            'size': 139654,
            'dedrm': False,
            'meta': {},
        },
    }

    # create the datastore and run a sync
    syncd_books = datastore.update_library(ebooks_dict, user)

    # assert book is new
    file_hash, data = syncd_books.items()[0]
    assert data['new'] is True, "wasn't stored on first sync"
    assert data['dupe'] is False, 'book should not be a duplicate'

    # sync again
    syncd_books = datastore.update_library(ebooks_dict, user)

    # assert book is duplicate
    file_hash, data = syncd_books.items()[0]
    assert data['dupe'] is True, 'book should be a duplicate'


def test_sync_ogre_id(datastore, rethinkdb, user):
    '''
    Test two basic syncs with the same book, supplying OGRE id in second sync
    as ogreclient should do
    '''
    ebooks_dict = {
        "H. C.\u0006Andersen\u0007Andersen's Fairy Tales": {
            'format': 'epub',
            'file_hash': 'b889dec9',
            'size': 139654,
            'dedrm': False,
            'meta': {},
        },
    }

    # create the datastore and run a sync
    syncd_books = datastore.update_library(ebooks_dict, user)

    # check book needs updating
    file_hash, data = syncd_books.items()[0]
    assert data['new'] is True, "wasn't stored on first sync"
    assert data['update'] is True, 'book should need update'
    assert 'ebook_id' in data, 'ebook_id should be present in ogreserver response'

    # set ogre_id in incoming data, same as ogreclient would
    ebooks_dict[ebooks_dict.keys()[0]]['meta']['ebook_id'] = data['ebook_id']

    # sync again
    syncd_books = datastore.update_library(ebooks_dict, user)

    # assert book does not need update
    file_hash, data = syncd_books.items()[0]
    assert data['update'] is False, 'book should not need update'


def test_sync_dupe_on_authortitle(datastore, rethinkdb, user):
    '''
    Test sync from two users with same book (different file hash)

    - Ensure the second sync attaches 2 versions to the single ebook_id
    - Ensure 2 versions are created on said ebook
    '''
    ebooks_dict = {
        "Lewis\u0006Carroll\u0007Alice's Adventures in Wonderland": {
            'format': 'epub',
            'file_hash': 'd41d8cd9',
            'size': 139654,
            'dedrm': False,
            'meta': {},
        },
    }

    # create the datastore and run a sync
    syncd_books = datastore.update_library(ebooks_dict, user)

    # extract ebook_id of syncd book
    ebook_id = syncd_books.itervalues().next()['ebook_id']

    assert rethinkdb.table('versions').filter(
        {'ebook_id': ebook_id}
    ).count().run() == 1, 'should be 1 version'

    # same book author/title, different file hash, from a different user
    ebooks_dict[ebooks_dict.keys()[0]]['file_hash'] = '058e92c0'

    # sync with diff user
    user.username = '2ndsync'
    syncd_books = datastore.update_library(ebooks_dict, user)

    # assert first sync ebook_id returned
    assert syncd_books.itervalues().next()['ebook_id'] == ebook_id

    # assert only one ebook in DB
    assert rethinkdb.table('ebooks').count().run() == 1, 'should only be 1 ebook'

    # assert ebook has two versions attached
    ebook = datastore.load_ebook(ebook_id)
    assert len(ebook['versions']) == 2, 'should be 2 versions'


def test_sync_dupe_on_ebookid(datastore, rethinkdb, user):
    '''
    Test sync from two users with same book (different file hash/authortitle);
    On the 2nd sync ebook_id is supplied

    - Ensure the second sync attaches 2 versions to the single ebook_id
    - Ensure 2 versions are created on said ebook
    '''
    ebooks_dict = {
        "Lewis\u0006Carroll\u0007Alice's Adventures in Wonderland": {
            'format': 'epub',
            'file_hash': 'd41d8cd9',
            'size': 139654,
            'dedrm': False,
            'meta': {},
        },
    }

    # create the datastore and run a sync
    syncd_books = datastore.update_library(ebooks_dict, user)

    # extract ebook_id of syncd book
    ebook_id = syncd_books.itervalues().next()['ebook_id']

    assert rethinkdb.table('versions').filter(
        {'ebook_id': ebook_id}
    ).count().run() == 1, 'should be 1 version'

    # different author/title
    ebooks_dict["Lewis\u0006Carroll\u0007Alice's Wonderland"] = ebooks_dict[ebooks_dict.keys()[0]]
    del(ebooks_dict["Lewis\u0006Carroll\u0007Alice's Adventures in Wonderland"])

    # supply ebook_id in second sync
    ebooks_dict[ebooks_dict.keys()[0]]['meta']['ebook_id'] = ebook_id

    # different file_hash, user
    ebooks_dict[ebooks_dict.keys()[0]]['file_hash'] = '058e92c0'

    # sync with diff user
    user.username = '2ndsync'
    syncd_books = datastore.update_library(ebooks_dict, user)

    # assert only one ebook in DB
    assert rethinkdb.table('ebooks').count().run() == 1, 'should only be 1 ebook'

    # assert ebook has two versions attached
    ebook = datastore.load_ebook(ebook_id)
    assert len(ebook['versions']) == 2, 'should be 2 versions'


def test_sync_dupe_on_original_hash(datastore, rethinkdb, user):
    '''
    Test sync from two users with same book (same file hash)
    (Ebooks' file_hash will change when adding OGRE_ID to metadata, so test
     that ogre still recognises this second sync as being duplicate)

    - Ensure the second sync rejects the duplicate
    - Ensure only a single version is attached to said ebook
    '''
    ebooks_dict = {
        u"Lewis\u0006Carroll\u0007Alice's Adventures in Wonderland": {
            'format': 'epub',
            'file_hash': 'd41d8cd9',
            'size': 139654,
            'dedrm': False,
            'meta': {},
        },
    }

    # create the datastore and run a sync
    syncd_books = datastore.update_library(ebooks_dict, user)

    # assert book is new
    file_hash, data = syncd_books.items()[0]
    assert data['new'] is True, "wasn't stored on first sync"
    assert data['dupe'] is False, 'book should not be a duplicate'

    # update file_hash post-metadata rewrite
    datastore.update_book_hash('d41d8cd9', '058e92c0')

    # sync with diff user
    user.username = '2ndsync'
    syncd_books = datastore.update_library(ebooks_dict, user)

    # assert book is duplicate
    file_hash, data = syncd_books.items()[0]
    assert data['dupe'] is True, 'book should be a duplicate'

    # assert ebook has single version attached
    ebook = datastore.load_ebook(data['ebook_id'])
    assert len(ebook['versions']) == 1, 'should be single version'
