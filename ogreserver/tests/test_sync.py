from __future__ import absolute_import
from __future__ import unicode_literals


def test_sync_duplicate(datastore, postgresql, rethinkdb, user, ebook_sync_fixture_1):
    '''
    Test two basic syncs with the same data. Book should be flagged as dupe
    '''
    # create the datastore and run a sync
    syncd_books = datastore.update_library(ebook_sync_fixture_1, user)

    # assert book is new
    file_hash, data = syncd_books.items()[0]
    assert data['new'] is True, "wasn't stored on first sync"
    assert data['dupe'] is False, 'book should not be a duplicate'

    # sync again
    syncd_books = datastore.update_library(ebook_sync_fixture_1, user)

    # assert book is duplicate
    file_hash, data = syncd_books.items()[0]
    assert data['dupe'] is True, 'book should be a duplicate'


def test_sync_ogre_id(datastore, postgresql, rethinkdb, user, ebook_sync_fixture_1):
    '''
    Test two basic syncs with the same book, supplying OGRE id in second sync
    as ogreclient should do
    '''
    # create the datastore and run a sync
    syncd_books = datastore.update_library(ebook_sync_fixture_1, user)

    # check book needs updating
    file_hash, data = syncd_books.items()[0]
    assert data['new'] is True, "wasn't stored on first sync"
    assert data['update'] is True, 'book should need update'
    assert 'ebook_id' in data, 'ebook_id should be present in ogreserver response'

    # set ogre_id in incoming data, same as ogreclient would
    ebook_sync_fixture_1.values()[0]['ebook_id'] = data['ebook_id']

    # sync again
    syncd_books = datastore.update_library(ebook_sync_fixture_1, user)

    # assert book does not need update
    file_hash, data = syncd_books.items()[0]
    assert data['update'] is False, 'book should not need update'


def test_sync_dupe_on_authortitle(datastore, postgresql, rethinkdb, user, user2, ebook_sync_fixture_1):
    '''
    Test sync from two users with same book (different file hash)

    - Ensure the second sync attaches 2 versions to the single ebook_id
    - Ensure 2 versions are created on said ebook
    - Ensure the book is marked with both owners
    '''
    # create the datastore and run a sync
    syncd_books = datastore.update_library(ebook_sync_fixture_1, user)

    # extract ebook_id of syncd book
    ebook_id = syncd_books.itervalues().next()['ebook_id']

    assert rethinkdb.table('versions').filter(
        {'ebook_id': ebook_id}
    ).count().run() == 1, 'should be 1 version'

    # same book author/title, different file hash, from a different user
    ebook_sync_fixture_1.values()[0]['file_hash'] = '058e92c0'

    # sync with diff user
    syncd_books = datastore.update_library(ebook_sync_fixture_1, user2)

    # assert first sync ebook_id returned
    assert syncd_books.itervalues().next()['ebook_id'] == ebook_id

    # assert only one ebook in DB
    assert rethinkdb.table('ebooks').count().run() == 1, 'should only be 1 ebook'

    # assert ebook has two versions attached
    ebook = datastore.load_ebook(ebook_id)
    assert len(ebook['versions']) == 2, 'should be 2 versions'

    # assert both users are owners (2 unique users)
    assert len({v['user']:None for v in ebook['versions']}.keys()) == 2


def test_sync_dupe_on_ebookid(datastore, postgresql, rethinkdb, user, user2, ebook_sync_fixture_1, ebook_sync_fixture_2):
    '''
    Test sync from two users with same book (different file hash/authortitle);
    On the 2nd sync ebook_id is supplied

    - Ensure the second sync attaches 2 versions to the single ebook_id
    - Ensure 2 versions are created on said ebook
    - Ensure the book is marked with both owners
    '''
    # create the datastore and run a sync
    syncd_books = datastore.update_library(ebook_sync_fixture_1, user)

    # extract ebook_id of syncd book
    ebook_id = syncd_books.itervalues().next()['ebook_id']

    assert rethinkdb.table('versions').filter(
        {'ebook_id': ebook_id}
    ).count().run() == 1, 'should be 1 version'

    # set second book to have same ebook_id
    ebook_sync_fixture_2.values()[0]['ebook_id'] = ebook_id

    # sync with diff user
    syncd_books = datastore.update_library(ebook_sync_fixture_2, user2)

    # assert only one ebook in DB
    assert rethinkdb.table('ebooks').count().run() == 1, 'should only be 1 ebook'

    # assert ebook has two versions attached
    ebook = datastore.load_ebook(ebook_id)
    assert len(ebook['versions']) == 2, 'should be 2 versions'

    # assert both users are owners (2 unique users)
    assert len({v['user']:None for v in ebook['versions']}.keys()) == 2


def test_sync_dupe_on_original_hash(datastore, postgresql, rethinkdb, user, user2, ebook_sync_fixture_1):
    '''
    Test sync from two users with same book (same file hash)
    (Ebooks' file_hash will change when adding OGRE_ID to metadata, so test
     that ogre still recognises this second sync as being duplicate)

    - Ensure the second sync rejects the duplicate
    - Ensure only a single version is attached to said ebook
    - Ensure the book is marked with both owners
    '''
    # create the datastore and run a sync
    syncd_books = datastore.update_library(ebook_sync_fixture_1, user)

    # assert book is new
    file_hash, data = syncd_books.items()[0]
    assert data['new'] is True, "wasn't stored on first sync"
    assert data['dupe'] is False, 'book should not be a duplicate'

    # update file_hash post-metadata rewrite
    datastore.update_ebook_hash('d41d8cd9', '058e92c0')

    # sync with diff user
    syncd_books = datastore.update_library(ebook_sync_fixture_1, user2)

    # assert book is duplicate
    file_hash, data = syncd_books.items()[0]
    assert data['dupe'] is True, 'book should be a duplicate'

    # assert ebook has single version attached
    ebook = datastore.load_ebook(data['ebook_id'])
    assert len(ebook['versions']) == 1, 'should be single version'

    # assert both users are owners of single format
    assert len(ebook['versions'][0]['formats'][0]['owners']) == 2


def test_sync_dupe_on_asin(datastore, postgresql, rethinkdb, user, ebook_sync_fixture_1, ebook_sync_fixture_2):
    '''
    Sync a book with ASIN set. Second sync should return duplicate.

    - Second sync has different authortitle, different file_hash
    - Ensure the second sync rejects the duplicate
    - Ensure only a single version is attached to said ebook
    '''
    # create the datastore and run a sync
    syncd_books = datastore.update_library(ebook_sync_fixture_1, user)

    # assert book is new
    file_hash, data = syncd_books.items()[0]
    assert data['new'] is True, "wasn't stored on first sync"
    assert data['dupe'] is False, 'book should not be a duplicate'

    # update other ebook to have same ASIN and sync that; it should be rejected
    ebook_sync_fixture_2.values()[0]['meta']['asin'] = ebook_sync_fixture_1.values()[0]['meta']['asin']

    # sync with a different book; matching ASIN
    syncd_books = datastore.update_library(ebook_sync_fixture_2, user)

    # assert book is duplicate
    file_hash, data = syncd_books.items()[0]
    assert data['dupe'] is True, 'book should be a duplicate'

    # assert ebook has single version attached
    ebook = datastore.load_ebook(data['ebook_id'])
    assert len(ebook['versions']) == 1, 'should be single version'


def test_sync_dupe_on_isbn(datastore, postgresql, rethinkdb, user, ebook_sync_fixture_1, ebook_sync_fixture_2):
    '''
    Sync a book with ISBN set. Second sync should return duplicate.

    - Second sync has different authortitle, different file_hash
    - Ensure the second sync attaches 2 versions to the single ebook_id
    - Ensure 2 versions are created on said ebook
    '''
    # create the datastore and run a sync
    syncd_books = datastore.update_library(ebook_sync_fixture_1, user)

    # assert book is new
    file_hash, data = syncd_books.items()[0]
    assert data['new'] is True, "wasn't stored on first sync"
    assert data['dupe'] is False, 'book should not be a duplicate'

    # update other ebook to have same ASIN and sync that; it should be rejected
    ebook_sync_fixture_2.values()[0]['meta']['isbn'] = ebook_sync_fixture_1.values()[0]['meta']['isbn']

    # sync with a different book; matching ISBN
    syncd_books = datastore.update_library(ebook_sync_fixture_2, user)

    # assert only one ebook in DB
    assert rethinkdb.table('ebooks').count().run() == 1, 'should only be 1 ebook'

    # assert ebook has two versions attached
    ebook = datastore.load_ebook(data['ebook_id'])
    assert len(ebook['versions']) == 2, 'should be 2 versions'


def test_meta(datastore, postgresql, rethinkdb, user, ebook_sync_fixture_1):
    '''
    Ensure all meta fields are applied to ebook on sync
    '''
    # create the datastore and run a sync
    syncd_books = datastore.update_library(ebook_sync_fixture_1, user)

    # extract ebook_id of syncd book
    ebook_id = syncd_books.values()[0]['ebook_id']

    # assert meta data
    ebook = datastore.load_ebook(ebook_id)
    assert ebook['meta']['asin'] == 'B00KG6MZ2O'
    assert ebook['meta']['isbn'] == '9781491999999'
    assert ebook['meta']['source']['provider'] == 'Amazon Kindle'
    assert ebook['meta']['source']['author'] == 'H. C. Andersen'
    assert ebook['meta']['source']['title'] == "Andersen's Fairy Tales"
