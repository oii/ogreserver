# coding: utf-8 -*-
from __future__ import absolute_import

import os

import pytest

from ogreclient.core import metadata_extract


def test_metadata_epub(calibre_ebook_meta_bin, ebook_lib_path):
    # Frankenstein
    meta = metadata_extract(calibre_ebook_meta_bin, os.path.join(ebook_lib_path, 'pg84.epub'))
    assert meta['author'] == 'Shelley, Mary Wollstonecraft'
    assert meta['title'] == 'Frankenstein'
    assert meta['uri'] == 'http://www.gutenberg.org/ebooks/84'

    # Beowulf
    meta = metadata_extract(calibre_ebook_meta_bin, os.path.join(ebook_lib_path, 'pg16328.epub'))
    assert meta['author'] == 'Unknown'
    assert meta['title'] == 'Beowulf / An Anglo-Saxon Epic Poem'
    assert meta['uri'] == 'http://www.gutenberg.org/ebooks/16328'

    # Wizard of Oz
    meta = metadata_extract(calibre_ebook_meta_bin, os.path.join(ebook_lib_path, 'pg55.epub'))
    assert meta['author'] == 'Baum, L. Frank (Lyman Frank)'
    assert meta['title'] == 'The Wonderful Wizard of Oz'
    assert meta['uri'] == 'http://www.gutenberg.org/ebooks/55'
    assert meta['tags'] == 'Fantasy, Oz (Imaginary place) -- Fiction'


def test_metadata_mobi(calibre_ebook_meta_bin, ebook_lib_path):
    # Wonderland, converted to mobi
    meta = metadata_extract(calibre_ebook_meta_bin, os.path.join(ebook_lib_path, 'pg11.mobi'))
    assert meta['author'] == 'Lewis Carroll'
    assert meta['title'] == "Alice's Adventures in Wonderland"
    assert meta['tags'] == 'Fantasy'
    assert meta['asin'] == '4373df90-da57-42de-9327-90f0e73e8e45'


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
