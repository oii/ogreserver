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
            'owner': 'mafro',
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
            'owner': 'mafro',
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
    ebooks_dict[ebooks_dict.keys()[0]]['ebook_id'] = data['ebook_id']

    # sync again
    syncd_books = datastore.update_library(ebooks_dict, user)

    # assert book does not need update
    file_hash, data = syncd_books.items()[0]
    assert data['update'] is False, 'book should not need update'


def test_sync_matching_authortitle(datastore, rethinkdb, user):
    '''
    Test a sync with different file hashes, but same author/title gives two versions
    '''
    ebooks_dict = {
        "Lewis\u0006Carroll\u0007Alice's Adventures in Wonderland": {
            'format': 'epub',
            'file_hash': 'd41d8cd9',
            'owner': 'mafro',
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

    # same book author/title, different file hash
    ebooks_dict[ebooks_dict.keys()[0]]['file_hash'] = '058e92c0'

    # sync again
    datastore.update_library(ebooks_dict, user)

    # assert only one ebook in DB
    assert rethinkdb.table('ebooks').count().run() == 1, 'should only be 1 ebook'

    # assert ebook has two versions attached
    assert rethinkdb.table('versions').filter(
        {'ebook_id': ebook_id}
    ).count().run() == 2, 'should be 2 versions'


def test_sync_matching_ogre_id(datastore, rethinkdb, user):
    '''
    Test a sync with different file hashes, but ogre_id/ebook_id supplied on second sync gives two versions
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
    ebooks_dict[ebooks_dict.keys()[0]]['ebook_id'] = ebook_id

    # different file_hash, user
    ebooks_dict[ebooks_dict.keys()[0]]['file_hash'] = '058e92c0'
    user.username = '2ndsync'

    # sync again
    datastore.update_library(ebooks_dict, user)

    # assert only one ebook in DB
    assert rethinkdb.table('ebooks').count().run() == 1, 'should only be 1 ebook'

    # assert ebook has two versions attached
    assert rethinkdb.table('versions').filter(
        {'ebook_id': ebook_id}
    ).count().run() == 2, 'should be 2 versions'


def test_sync_matching_original_hash(datastore, rethinkdb, user):
    '''
    Since ebooks have their meta data rewritten when adding OGRE_ID, the file hash
    will change. Ensure that we match up incoming duplicates.
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

    # sync again, using same source file_hash, and no ogre_id in metadata
    syncd_books = datastore.update_library(ebooks_dict, user)

    # assert book is duplicate
    file_hash, data = syncd_books.items()[0]
    assert data['dupe'] is True, 'book should be a duplicate'

    # assert ebook has single version attached
    assert rethinkdb.table('versions').filter(
        {'ebook_id': data['ebook_id']}
    ).count().run() == 1, 'should be single version'
