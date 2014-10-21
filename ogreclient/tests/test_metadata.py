# coding: utf-8 -*-
from __future__ import absolute_import

import os
import shutil

import mock
import pytest


@pytest.mark.requires_calibre
def test_metadata_epub(helper_get_ebook):
    # Frankenstein
    ebook_obj = helper_get_ebook('pg84.epub')
    assert ebook_obj.meta['firstname'] == u'Mary Wollstonecraft'
    assert ebook_obj.meta['lastname'] == u'Shelley'
    assert ebook_obj.meta['title'] == u'Frankenstein'
    assert ebook_obj.meta['uri'] == u'http://www.gutenberg.org/ebooks/84'

    # Beowulf
    ebook_obj = helper_get_ebook('pg16328.epub')
    assert ebook_obj.meta['lastname'] == u'Unknown'
    assert ebook_obj.meta['title'] == u'Beowulf / An Anglo-Saxon Epic Poem'
    assert ebook_obj.meta['uri'] == u'http://www.gutenberg.org/ebooks/16328'

    # Wizard of Oz
    ebook_obj = helper_get_ebook('pg55.epub')
    assert ebook_obj.meta['firstname'] == u'L. Frank (Lyman Frank)'
    assert ebook_obj.meta['lastname'] == u'Baum'
    assert ebook_obj.meta['title'] == u'The Wonderful Wizard of Oz'
    assert ebook_obj.meta['uri'] == u'http://www.gutenberg.org/ebooks/55'
    assert ebook_obj.meta['tags'] == u'Fantasy, Oz (Imaginary place) -- Fiction'


@pytest.mark.requires_calibre
def test_metadata_mobi(helper_get_ebook):
    # Wonderland, converted to mobi
    ebook_obj = helper_get_ebook('pg11.mobi')
    assert ebook_obj.meta['firstname'] == u'Lewis'
    assert ebook_obj.meta['lastname'] == u'Carroll'
    assert ebook_obj.meta['title'] == u"Alice's Adventures in Wonderland"
    assert ebook_obj.meta['tags'] == u'Fantasy'
    assert ebook_obj.meta['asin'] == u'4373df90-da57-42de-9327-90f0e73e8e45'


@pytest.mark.requires_calibre
def test_metadata_utf8(helper_get_ebook):
    # Wuthering Heights
    ebook_obj = helper_get_ebook('pg768.epub')
    assert ebook_obj.meta['firstname'] == u'Emily'
    assert ebook_obj.meta['lastname'] == u'Brontë'


def test_parse_authortitle(parse_author_method):
    # double-barrelled firstname
    firstname, lastname = parse_author_method('H. C. Andersen')
    for var in (firstname, lastname):
        assert type(var) is unicode
    assert firstname == u'H. C.'
    assert lastname == u'Andersen'

    # UTF-8 encoded lastname
    firstname, lastname = parse_author_method('Emily Bront\xc3\xab')
    for var in (firstname, lastname):
        assert type(var) is unicode
    assert firstname == u'Emily'
    assert lastname == u'Brontë'

    # comma-separated lastname, firstname
    firstname, lastname = parse_author_method('Carroll, Lewis')
    for var in (firstname, lastname):
        assert type(var) is unicode
    assert firstname == u'Lewis'
    assert lastname == u'Carroll'

    # comma-separated lastname, firstname in appended brackets
    firstname, lastname = parse_author_method('Lewis Carroll [Carroll, Lewis]')
    for var in (firstname, lastname):
        assert type(var) is unicode
    assert firstname == u'Lewis'
    assert lastname == u'Carroll'

    # comma-separated lastname, firstname & double-barrelled firstname
    firstname, lastname = parse_author_method('Andersen, H. C.')
    for var in (firstname, lastname):
        assert type(var) is unicode
    assert firstname == u'H. C.'
    assert lastname == u'Andersen'


@pytest.mark.requires_calibre
def test_metadata_dedrm(helper_get_ebook, ebook_lib_path, tmpdir):
    # stick Alice in Wonderland into a tmpdir
    shutil.copy(os.path.join(ebook_lib_path, 'pg11.epub'), tmpdir.strpath)

    ebook_obj = helper_get_ebook('pg11.epub', basepath=tmpdir.strpath)

    # add DeDRM tag to test epub
    ebook_obj.add_dedrm_tag()

    # verify that ogre_id is on the epub
    ebook_obj.get_metadata()
    assert 'uri' in ebook_obj.meta.keys()
    assert hasattr(ebook_obj, 'drmfree')
    assert 'OGRE-DeDRM' not in ebook_obj.meta['tags']


@pytest.mark.requires_calibre
def test_metadata_ogreid_epub(mock_urlopen, helper_get_ebook, ebook_lib_path, tmpdir):
    # mock return from urlopen().read()
    mock_urlopen.return_value = mock.Mock()
    mock_urlopen.return_value.read.return_value = 'ok'

    # stick Alice in Wonderland into a tmpdir
    shutil.copy(os.path.join(ebook_lib_path, 'pg11.epub'), tmpdir.strpath)

    ebook_obj = helper_get_ebook('pg11.epub', basepath=tmpdir.strpath)

    # add ogre_id to test epub
    ebook_obj.add_ogre_id_tag(
        ogre_id='egg',
        session_key='thisisnotakey',
    )

    # verify that ogre_id is on the epub
    ebook_obj.get_metadata()
    assert 'uri' in ebook_obj.meta.keys()
    assert 'ebook_id' in ebook_obj.meta.keys()
    assert ebook_obj.meta['ebook_id'] == 'egg'


@pytest.mark.requires_calibre
def test_metadata_ogreid_mobi(mock_urlopen, helper_get_ebook, ebook_lib_path, tmpdir):
    # mock return from urlopen().read()
    mock_urlopen.return_value = mock.Mock()
    mock_urlopen.return_value.read.return_value = 'ok'

    # stick Alice in Wonderland into a tmpdir
    shutil.copy(os.path.join(ebook_lib_path, 'pg11.mobi'), tmpdir.strpath)

    ebook_obj = helper_get_ebook('pg11.mobi', basepath=tmpdir.strpath)

    # test tags field
    ebook_obj.meta['tags'] = 'Fantasy'

    # add ogre_id to test mobi
    ebook_obj.add_ogre_id_tag(
        ogre_id='egg',
        session_key='thisisnotakey',
    )

    # verify that ogre_id is on the mobi
    ebook_obj.get_metadata()
    assert 'ebook_id' in ebook_obj.meta
    assert ebook_obj.meta['ebook_id'] == 'egg'
    assert ebook_obj.meta['tags'] == 'Fantasy'
    assert 'ogre_id' not in ebook_obj.meta['tags']


@pytest.mark.requires_calibre
def test_metadata_ogreid_mobi_utf8(mock_urlopen, helper_get_ebook, ebook_lib_path, tmpdir):
    # mock return from urlopen().read()
    mock_urlopen.return_value = mock.Mock()
    mock_urlopen.return_value.read.return_value = 'ok'

    # stick Alice in Wonderland into a tmpdir
    shutil.copy(os.path.join(ebook_lib_path, 'pg11.mobi'), tmpdir.strpath)

    ebook_obj = helper_get_ebook('pg11.mobi', basepath=tmpdir.strpath)

    # test tags field
    ebook_obj.meta['tags'] = 'diaëresis'

    # mobi books add ogre_id it --tags
    ebook_obj.add_ogre_id_tag(
        ogre_id='egg',
        session_key='thisisnotakey',
    )

    # verify that --tags still has the UTF-8
    ebook_obj.get_metadata()
    assert ebook_obj.meta['tags'] == u'diaëresis'
