from __future__ import absolute_import
from __future__ import unicode_literals

from ..exceptions import NoFormatAvailableError

import pytest


def test_get_ebook_filehash_specific_format(datastore, user, rethinkdb):
    # create test ebook data directly in rethinkdb
    rethinkdb.table('ebooks').insert({
        'author': 'H. C. Andersen',
        'title': "Andersen's Fairy Tales",
        'ebook_id': 'bcddb7988cf91f7025dd778ca49ecf9f'
    }).run()

    # use the datastore API to create version/format
    version_id = datastore._create_new_version('bcddb7988cf91f7025dd778ca49ecf9f', user.username, {
        'format': 'epub',
        'file_hash': '38b3fc3a',
        'size': 1234,
        'dedrm': False,
    })

    # mark single format as uploaded
    rethinkdb.table('formats').get('38b3fc3a').update({'uploaded': True}).run()

    file_hash = datastore._get_ebook_filehash(
        'bcddb7988cf91f7025dd778ca49ecf9f',
        version_id=version_id,
        fmt='epub'
    )

    # assert filehash is from the first version in rethinkdb
    assert file_hash == '38b3fc3a'


def test_get_ebook_filehash_none_uploaded(datastore, user, rethinkdb):
    # create test ebook data directly in rethinkdb
    rethinkdb.table('ebooks').insert({
        'author': 'H. C. Andersen',
        'title': "Andersen's Fairy Tales",
        'ebook_id': 'bcddb7988cf91f7025dd778ca49ecf9f'
    }).run()

    # use the datastore API to create version/format
    version_id = datastore._create_new_version('bcddb7988cf91f7025dd778ca49ecf9f', user.username, {
        'format': 'epub',
        'file_hash': '38b3fc3a',
        'size': 1234,
        'dedrm': False,
    })

    # assert exception since no formats are marked as 'uploaded'
    with pytest.raises(NoFormatAvailableError):
        datastore._get_ebook_filehash(
            'bcddb7988cf91f7025dd778ca49ecf9f',
            version_id=version_id,
            fmt='epub'
        )


def test_get_ebook_filehash_user_preferred_format(datastore, user, rethinkdb):
    # create test ebook data directly in rethinkdb
    rethinkdb.table('ebooks').insert({
        'author': 'H. C. Andersen',
        'title': "Andersen's Fairy Tales",
        'ebook_id': 'bcddb7988cf91f7025dd778ca49ecf9f'
    }).run()

    # use the datastore API to create version/format
    version_id = datastore._create_new_version('bcddb7988cf91f7025dd778ca49ecf9f', user.username, {
        'format': 'epub',
        'file_hash': '38b3fc3a',
        'size': 1234,
        'dedrm': False,
    })

    # mark first format as uploaded
    rethinkdb.table('formats').get('38b3fc3a').update({'uploaded': True}).run()

    # create another format against the single version
    rethinkdb.table('formats').insert({
        'file_hash': 'f7025dd7',
        'version_id': version_id,
        'format': 'mobi',
        'user': user.username,
        'uploaded': True,
    }).run()

    # test user.preferred_ebook_format == 'mobi'
    file_hash = datastore._get_ebook_filehash(
        'bcddb7988cf91f7025dd778ca49ecf9f',
        version_id=version_id,
        user=user
    )

    # assert filehash is from the first version in rethinkdb
    assert file_hash == 'f7025dd7'


def test_get_ebook_filehash_OGRE_preferred_format(datastore, user, rethinkdb):
    # create test ebook data directly in rethinkdb
    rethinkdb.table('ebooks').insert({
        'author': 'H. C. Andersen',
        'title': "Andersen's Fairy Tales",
        'ebook_id': 'bcddb7988cf91f7025dd778ca49ecf9f'
    }).run()

    # use the datastore API to create version/format
    version_id = datastore._create_new_version('bcddb7988cf91f7025dd778ca49ecf9f', user.username, {
        'format': 'egg',
        'file_hash': '38b3fc3a',
        'size': 1234,
        'dedrm': False,
    })

    # mark first format as uploaded
    rethinkdb.table('formats').get('38b3fc3a').update({'uploaded': True}).run()

    # create another format against the single version
    rethinkdb.table('formats').insert({
        'file_hash': 'f7025dd7',
        'version_id': version_id,
        'format': 'mobi',
        'user': user.username,
        'uploaded': True,
    }).run()

    # test OGRE's EBOOK_FORMATS config supplies 'egg' top
    file_hash = datastore._get_ebook_filehash(
        'bcddb7988cf91f7025dd778ca49ecf9f',
        version_id=version_id
    )

    # assert filehash is from the first version in rethinkdb
    assert file_hash == '38b3fc3a'


def test_get_ebook_filehash_uploaded(datastore, user, rethinkdb):
    # create test ebook data directly in rethinkdb
    rethinkdb.table('ebooks').insert({
        'author': 'H. C. Andersen',
        'title': "Andersen's Fairy Tales",
        'ebook_id': 'bcddb7988cf91f7025dd778ca49ecf9f'
    }).run()

    # use the datastore API to create version/format
    version_id = datastore._create_new_version('bcddb7988cf91f7025dd778ca49ecf9f', user.username, {
        'format': 'egg',
        'file_hash': '38b3fc3a',
        'size': 1234,
        'dedrm': False,
    })

    # create another format against the single version
    rethinkdb.table('formats').insert({
        'file_hash': 'f7025dd7',
        'version_id': version_id,
        'format': 'egg',
        'user': user.username,
        'uploaded': True,
    }).run()

    # test get file_hash for format where uploaded is True
    file_hash = datastore._get_ebook_filehash(
        'bcddb7988cf91f7025dd778ca49ecf9f',
        version_id=version_id
    )

    # assert filehash is from the first version in rethinkdb
    assert file_hash == 'f7025dd7'
