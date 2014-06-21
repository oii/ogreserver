# coding: utf-8 -*-
from __future__ import absolute_import

import os

import pytest

from ogreclient.core import metadata_extract


def test_metadata_epub(calibre_ebook_meta_bin, ebook_lib_path):
    # Frankenstein
    meta = metadata_extract(calibre_ebook_meta_bin, os.path.join(ebook_lib_path, 'pg84.epub'))
    assert meta['author'] == 'Shelley, Mary Wollstonecraft'

    # Beowulf
    meta = metadata_extract(calibre_ebook_meta_bin, os.path.join(ebook_lib_path, 'pg16328.epub'))
    assert meta['author'] == 'Unknown'


def test_metadata_mobi(calibre_ebook_meta_bin, ebook_lib_path):
    # Wonderland, converted to mobi
    meta = metadata_extract(calibre_ebook_meta_bin, os.path.join(ebook_lib_path, 'pg11.mobi'))
    assert meta['author'] == 'Lewis Carroll'


def test_metadata_utf8(calibre_ebook_meta_bin, ebook_lib_path):
    # Wuthering Heights
    meta = metadata_extract(calibre_ebook_meta_bin, os.path.join(ebook_lib_path, 'pg768.epub'))
    assert meta['author'] == u'Brontë, Emily'


@pytest.mark.xfail
def test_metadata_drm(calibre_ebook_meta_bin, ebook_lib_path):
    pass


@pytest.mark.xfail
def test_metadata_ogre_id(calibre_ebook_meta_bin, ebook_lib_path):
    pass
