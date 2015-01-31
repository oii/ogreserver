# coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals

import pytest


def test_generate_filename(datastore):
    # ensure exception raised on non-unicode string passed
    with pytest.raises(UnicodeWarning):
        filename = datastore.generate_filename(
            '38b3fc3aa7fe67e76f0d8b248e62b940',
            author=str('H. C.'),
        )

    filename = datastore.generate_filename(
        '38b3fc3aa7fe67e76f0d8b248e62b940',
        author='H. C. Andersen',
        title="Andersen's Fairy Tales",
        format='epub'
    )
    assert filename == 'H_C_Andersen__Andersens_Fairy_Tales.38b3fc3a.epub'

    filename = datastore.generate_filename(
        '38b3fc3aa7fe67e76f0d8b248e62b940',
        author='H. C. (Hans Christian) Andersen',
        title="Andersen's Fairy Tales",
        format='epub'
    )
    assert filename == 'H_C_Hans_Christian_Andersen__Andersens_Fairy_Tales.38b3fc3a.epub'


def test_generate_filename_transpose(datastore):
    # test unicode transcode
    filename = datastore.generate_filename(
        '38b3fc3aa7fe67e76f0d8b248e62b940',
        author='Emily Brontë',
        title='Wuthering Heights',
        format='epub'
    )

    assert 'Bronte' in filename, 'transcode of ë failed'


def test_generate_filename_with_db_load(datastore, rethinkdb, user):
    # create test ebook data directly in rethinkdb
    rethinkdb.table('ebooks').insert({
        'author': 'H. C. Andersen',
        'title': "Andersen's Fairy Tales",
        'ebook_id': 'bcddb7988cf91f7025dd778ca49ecf9f'
    }).run()
    datastore._create_new_version('bcddb7988cf91f7025dd778ca49ecf9f', user.username, {
        'format': 'epub',
        'file_hash': '38b3fc3aa7fe67e76f0d8b248e62b940',
        'size': 1234,
        'dedrm': False,
    })

    # test filename generate when supplying only an MD5
    filename = datastore.generate_filename('38b3fc3aa7fe67e76f0d8b248e62b940')
    assert filename == 'H_C_Andersen__Andersens_Fairy_Tales.38b3fc3a.epub'

    # test filename generate with everything except format
    filename = datastore.generate_filename(
        '38b3fc3aa7fe67e76f0d8b248e62b940',
        author='H. C. Andersen',
        title="Andersen's Fairy Tales"
    )
    assert filename == 'H_C_Andersen__Andersens_Fairy_Tales.38b3fc3a.epub'
