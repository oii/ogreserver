# coding: utf-8 -*-
from __future__ import absolute_import

import os
import shutil

import mock
import pytest

from ogreclient.core import metadata_extract, add_ogre_id_to_ebook


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


def test_metadata_ogre_id_epub(mock_urlopen, calibre_ebook_meta_bin, ebook_lib_path, tmpdir):
    # mock return from urlopen().read()
    mock_urlopen.return_value = mock.Mock()
    mock_urlopen.return_value.read.return_value = 'ok'

    # stick Alice in Wonderland into a tmpdir
    shutil.copy(os.path.join(ebook_lib_path, 'pg11.epub'), tmpdir.strpath)

    # add ogre_id to test epub
    add_ogre_id_to_ebook(
        calibre_ebook_meta_bin,
        file_md5='egg',
        filepath=os.path.join(tmpdir.strpath, 'pg11.epub'),
        existing_tags='',
        ogre_id='egg',
        host='example.com',
        session_key='thisisnotakey',
    )

    # verify that ogre_id is on the epub
    meta = metadata_extract(calibre_ebook_meta_bin, os.path.join(tmpdir.strpath, 'pg11.epub'))
    assert 'ebook_id' in meta.keys()
    assert meta['ebook_id'] == 'egg'


def test_metadata_ogre_id_mobi(mock_urlopen, calibre_ebook_meta_bin, ebook_lib_path, tmpdir):
    # mock return from urlopen().read()
    mock_urlopen.return_value = mock.Mock()
    mock_urlopen.return_value.read.return_value = 'ok'

    # stick Alice in Wonderland into a tmpdir
    shutil.copy(os.path.join(ebook_lib_path, 'pg11.mobi'), tmpdir.strpath)

    # add ogre_id to test mobi
    add_ogre_id_to_ebook(
        calibre_ebook_meta_bin,
        file_md5='egg',
        filepath=os.path.join(tmpdir.strpath, 'pg11.mobi'),
        existing_tags='Fantasy',
        ogre_id='egg',
        host='example.com',
        session_key='thisisnotakey',
    )

    # verify that ogre_id is on the mobi
    meta = metadata_extract(calibre_ebook_meta_bin, os.path.join(tmpdir.strpath, 'pg11.mobi'))
    assert 'ebook_id' in meta
    assert meta['ebook_id'] == 'egg'
    assert meta['tags'] == 'Fantasy'


def test_metadata_ogre_id_mobi_utf8(mock_urlopen, calibre_ebook_meta_bin, ebook_lib_path, tmpdir):
    # mock return from urlopen().read()
    mock_urlopen.return_value = mock.Mock()
    mock_urlopen.return_value.read.return_value = 'ok'

    # stick Alice in Wonderland into a tmpdir
    shutil.copy(os.path.join(ebook_lib_path, 'pg11.mobi'), tmpdir.strpath)

    # mobi books add ogre_id it --tags
    add_ogre_id_to_ebook(
        calibre_ebook_meta_bin,
        file_md5='egg',
        filepath=os.path.join(tmpdir.strpath, 'pg11.mobi'),
        existing_tags=u'diaëresis',
        ogre_id='egg',
        host='example.com',
        session_key='thisisnotakey',
    )

    # verify that --tags still has the UTF-8
    meta = metadata_extract(calibre_ebook_meta_bin, os.path.join(tmpdir.strpath, 'pg11.mobi'))
    assert meta['tags'] == u'diaëresis'
