# coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals

import pytest


def test_generate_filename_unicode_error(datastore):
    # ensure exception raised on non-unicode string passed
    with pytest.raises(UnicodeWarning):
        datastore._generate_filename(
            '38b3fc3aa7fe67e76f0d8b248e62b940',
            author=str('H. C.'),
        )


def test_generate_filename_short_name(datastore):
    filename = datastore._generate_filename(
        '38b3fc3aa7fe67e76f0d8b248e62b940',
        author='H. C. Andersen',
        title="Andersen's Fairy Tales",
        fmt='epub',
    )
    assert filename == 'H_C_Andersen__Andersens_Fairy_Tales.38b3fc3a.epub'


def test_generate_filename_extended_name(datastore):
    filename = datastore._generate_filename(
        '38b3fc3aa7fe67e76f0d8b248e62b940',
        author='H. C. (Hans Christian) Andersen',
        title="Andersen's Fairy Tales",
        fmt='epub',
    )
    assert filename == 'H_C_Hans_Christian_Andersen__Andersens_Fairy_Tales.38b3fc3a.epub'


def test_generate_filename_transpose(datastore):
    # test unicode transcode
    filename = datastore._generate_filename(
        '38b3fc3aa7fe67e76f0d8b248e62b940',
        author='Emily Brontë',
        title='Wuthering Heights',
        fmt='epub',
    )

    assert 'Bronte' in filename, 'transcode of ë failed'


def test_generate_filename_from_file_hash(datastore, postgresql, user, ebook_fixture_azw3):
    # create test ebook data
    ebook = datastore.create_ebook(
        "Andersen's Fairy Tales", 'H. C. Andersen', user, ebook_fixture_azw3
    )

    filename = datastore._generate_filename(
        ebook.original_version.source_format.file_hash,
    )
    assert filename == 'H_C_Andersen__Andersens_Fairy_Tales.6c9376c4.azw3'
