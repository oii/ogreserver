# coding: utf-8 -*-
from __future__ import absolute_import

import os
import shutil

import mock
import pytest

from ogreclient.core import metadata_extract, _parse_author, add_ogre_id_to_ebook


def test_metadata_epub(calibre_ebook_meta_bin, ebook_lib_path):
    # Frankenstein
    meta = metadata_extract(calibre_ebook_meta_bin, os.path.join(ebook_lib_path, 'pg84.epub'))
    assert meta['firstname'] == u'Mary Wollstonecraft'
    assert meta['lastname'] == u'Shelley'
    assert meta['title'] == u'Frankenstein'
    assert meta['uri'] == u'http://www.gutenberg.org/ebooks/84'

    # Beowulf
    meta = metadata_extract(calibre_ebook_meta_bin, os.path.join(ebook_lib_path, 'pg16328.epub'))
    assert meta['lastname'] == u'Unknown'
    assert meta['title'] == u'Beowulf / An Anglo-Saxon Epic Poem'
    assert meta['uri'] == u'http://www.gutenberg.org/ebooks/16328'

    # Wizard of Oz
    meta = metadata_extract(calibre_ebook_meta_bin, os.path.join(ebook_lib_path, 'pg55.epub'))
    assert meta['firstname'] == u'L. Frank (Lyman Frank)'
    assert meta['lastname'] == u'Baum'
    assert meta['title'] == u'The Wonderful Wizard of Oz'
    assert meta['uri'] == u'http://www.gutenberg.org/ebooks/55'
    assert meta['tags'] == u'Fantasy, Oz (Imaginary place) -- Fiction'


def test_metadata_mobi(calibre_ebook_meta_bin, ebook_lib_path):
    # Wonderland, converted to mobi
    meta = metadata_extract(calibre_ebook_meta_bin, os.path.join(ebook_lib_path, 'pg11.mobi'))
    assert meta['firstname'] == u'Lewis'
    assert meta['lastname'] == u'Carroll'
    assert meta['title'] == u"Alice's Adventures in Wonderland"
    assert meta['tags'] == u'Fantasy'
    assert meta['asin'] == u'4373df90-da57-42de-9327-90f0e73e8e45'


def test_metadata_utf8(calibre_ebook_meta_bin, ebook_lib_path):
    # Wuthering Heights
    meta = metadata_extract(calibre_ebook_meta_bin, os.path.join(ebook_lib_path, 'pg768.epub'))
    assert meta['firstname'] == u'Emily'
    assert meta['lastname'] == u'Brontë'


def test_parse_authortitle():
    # double-barrelled firstname
    firstname, lastname = _parse_author("H. C. Andersen")
    for var in (firstname, lastname):
        assert type(var) is unicode
    assert firstname == u'H. C.'
    assert lastname == u'Andersen'

    # UTF-8 encoded lastname
    firstname, lastname = _parse_author('Emily Bront\xc3\xab')
    for var in (firstname, lastname):
        assert type(var) is unicode
    assert firstname == u'Emily'
    assert lastname == u'Brontë'

    # comma-separated lastname, firstname
    firstname, lastname = _parse_author("Carroll, Lewis")
    for var in (firstname, lastname):
        assert type(var) is unicode
    assert firstname == u'Lewis'
    assert lastname == u'Carroll'

    # comma-separated lastname, firstname in appended brackets
    firstname, lastname = _parse_author("Lewis Carroll [Carroll, Lewis]")
    for var in (firstname, lastname):
        assert type(var) is unicode
    assert firstname == u'Lewis'
    assert lastname == u'Carroll'

    # comma-separated lastname, firstname & double-barrelled firstname
    firstname, lastname = _parse_author("Andersen, H. C.")
    for var in (firstname, lastname):
        assert type(var) is unicode
    assert firstname == u'H. C.'
    assert lastname == u'Andersen'


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
        file_hash='egg',
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
        file_hash='egg',
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
        file_hash='egg',
        filepath=os.path.join(tmpdir.strpath, 'pg11.mobi'),
        existing_tags=u'diaëresis',
        ogre_id='egg',
        host='example.com',
        session_key='thisisnotakey',
    )

    # verify that --tags still has the UTF-8
    meta = metadata_extract(calibre_ebook_meta_bin, os.path.join(tmpdir.strpath, 'pg11.mobi'))
    assert meta['tags'] == u'diaëresis'
