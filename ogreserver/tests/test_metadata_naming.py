# coding: utf-8 -*-
from __future__ import absolute_import

from ..models.datastore import DataStore

import pytest


def test_generate_filename(flask_app):
    ds = DataStore(flask_app.config, flask_app.logger)

    # ensure exception raised on non-unicode string passed
    with pytest.raises(UnicodeWarning):
        filename = ds.generate_filename(
            '38b3fc3aa7fe67e76f0d8b248e62b940',
            firstname='H. C.',
        )

    filename = ds.generate_filename(
        '38b3fc3aa7fe67e76f0d8b248e62b940',
        firstname=u'H. C.',
        lastname=u'Andersen',
        title=u"Andersen's Fairy Tales",
        format='epub'
    )
    assert filename == 'H_C_Andersen__Andersens_Fairy_Tales.38b3fc3a.epub'

    filename = ds.generate_filename(
        '38b3fc3aa7fe67e76f0d8b248e62b940',
        firstname=u'H. C. (Hans Christian)',
        lastname=u'Andersen',
        title=u"Andersen's Fairy Tales",
        format='epub'
    )
    assert filename == 'H_C_Hans_Christian_Andersen__Andersens_Fairy_Tales.38b3fc3a.epub'


def test_generate_filename_transpose(flask_app):
    ds = DataStore(flask_app.config, flask_app.logger)

    # test unicode transcode
    filename = ds.generate_filename(
        '38b3fc3aa7fe67e76f0d8b248e62b940',
        firstname=u'Emily',
        lastname='Bront\xc3\xab'.decode('UTF-8'),
        title=u'Wuthering Heights',
        format='epub'
    )

    assert 'Bronte' in filename, u'transcode of ë failed'


def test_generate_filename_with_db_load(flask_app, rethinkdb, user):
    ebooks_dict = {
        u"H. C.\u0006Andersen\u0007Andersen's Fairy Tales": {
            'format': 'epub',
            'file_hash': '38b3fc3aa7fe67e76f0d8b248e62b940',
            'owner': 'mafro',
            'size': 139654,
            'dedrm': False,
        },
    }

    # create the datastore and run a sync
    ds = DataStore(flask_app.config, flask_app.logger)
    ds.update_library(ebooks_dict, user)

    # test filename generate when supplying only an MD5
    filename = ds.generate_filename('38b3fc3aa7fe67e76f0d8b248e62b940')
    assert filename == 'H_C_Andersen__Andersens_Fairy_Tales.38b3fc3a.epub'

    # test filename generate with everything except format
    filename = ds.generate_filename(
        '38b3fc3aa7fe67e76f0d8b248e62b940',
        firstname=u'H. C.',
        lastname=u'Andersen',
        title=u"Andersen's Fairy Tales"
    )
    assert filename == 'H_C_Andersen__Andersens_Fairy_Tales.38b3fc3a.epub'
