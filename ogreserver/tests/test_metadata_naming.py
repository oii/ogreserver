# coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals

import pytest

from ogreserver.stores import s3 as s3_store


def test_generate_filename_unicode_error():
    # ensure exception raised on non-unicode string passed
    with pytest.raises(UnicodeWarning):
        s3_store._generate_filename(
            '38b3fc3aa7fe67e76f0d8b248e62b940',
            author=str('H. C.'),
        )


def test_generate_filename_short_name():
    filename = s3_store._generate_filename(
        '38b3fc3aa7fe67e76f0d8b248e62b940',
        author='H. C. Andersen',
        title="Andersen's Fairy Tales",
        fmt='epub',
    )
    assert filename == 'H_C_Andersen__Andersens_Fairy_Tales.38b3fc3a.epub'


def test_generate_filename_extended_name():
    filename = s3_store._generate_filename(
        '38b3fc3aa7fe67e76f0d8b248e62b940',
        author='H. C. (Hans Christian) Andersen',
        title="Andersen's Fairy Tales",
        fmt='epub',
    )
    assert filename == 'H_C_Hans_Christian_Andersen__Andersens_Fairy_Tales.38b3fc3a.epub'


def test_generate_filename_extended_name_with_brackets():
    filename = s3_store._generate_filename(
        'c9850dc5a1d016816baa88ae86be627b',
        author='Joe Abercrombie',
        title='Half a War (Shattered Sea, #3)',
        fmt='epub',
    )
    assert filename == 'Joe_Abercrombie__Half_a_War_Shattered_Sea_3.c9850dc5.epub'


def test_generate_filename_transpose():
    # test unicode transcode
    filename = s3_store._generate_filename(
        '38b3fc3aa7fe67e76f0d8b248e62b940',
        author='Emily Brontë',
        title='Wuthering Heights',
        fmt='epub',
    )

    assert 'Bronte' in filename, 'transcode of ë failed'


def test_generate_filename_from_file_hash(postgresql, user, ebook_db_fixture_azw3):
    filename = s3_store._generate_filename(
        ebook_db_fixture_azw3.original_version.source_format.file_hash,
    )
    assert filename == 'H_C_Andersen__Andersens_Fairy_Tales.6c9376c4.azw3'
