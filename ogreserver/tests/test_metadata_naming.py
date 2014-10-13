# coding: utf-8 -*-
from __future__ import absolute_import

import pytest


def test_generate_filename(datastore):
    # ensure exception raised on non-unicode string passed
    with pytest.raises(UnicodeWarning):
        filename = datastore.generate_filename(
            '38b3fc3aa7fe67e76f0d8b248e62b940',
            firstname='H. C.',
        )

    filename = datastore.generate_filename(
        '38b3fc3aa7fe67e76f0d8b248e62b940',
        firstname=u'H. C.',
        lastname=u'Andersen',
        title=u"Andersen's Fairy Tales",
        format='epub'
    )
    assert filename == 'H_C_Andersen__Andersens_Fairy_Tales.38b3fc3a.epub'

    filename = datastore.generate_filename(
        '38b3fc3aa7fe67e76f0d8b248e62b940',
        firstname=u'H. C. (Hans Christian)',
        lastname=u'Andersen',
        title=u"Andersen's Fairy Tales",
        format='epub'
    )
    assert filename == 'H_C_Hans_Christian_Andersen__Andersens_Fairy_Tales.38b3fc3a.epub'


def test_generate_filename_transpose(datastore):
    # test unicode transcode
    filename = datastore.generate_filename(
        '38b3fc3aa7fe67e76f0d8b248e62b940',
        firstname=u'Emily',
        lastname='Bront\xc3\xab'.decode('UTF-8'),
        title=u'Wuthering Heights',
        format='epub'
    )

    assert 'Bronte' in filename, u'transcode of ë failed'


def test_generate_filename_with_db_load(datastore, rethinkdb, user):
    # create test ebook data directly in rethinkdb
    rethinkdb.table('ebooks').insert({
        'firstname': 'H. C.',
        'lastname': 'Andersen',
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
        firstname=u'H. C.',
        lastname=u'Andersen',
        title=u"Andersen's Fairy Tales"
    )
    assert filename == 'H_C_Andersen__Andersens_Fairy_Tales.38b3fc3a.epub'
