# coding: utf-8 -*-
from __future__ import absolute_import

from ..models.datastore import DataStore


def test_parse_authortitle(flask_app):
    ds = DataStore(flask_app.config, flask_app.logger)

    # double-barrelled firstname
    firstname, lastname, title = ds._parse_author_title("H. C. Andersen - Andersen's Fairy Tales")
    for var in (firstname, lastname, title):
        assert type(var) is unicode
    assert firstname == u'H. C.'
    assert lastname == u'Andersen'
    assert title == u"Andersen's Fairy Tales"

    # UTF-8 encoded lastname
    firstname, lastname, title = ds._parse_author_title('Emily Bront\xc3\xab - Wuthering Heights')
    for var in (firstname, lastname, title):
        assert type(var) is unicode
    assert firstname == u'Emily'
    assert lastname == u'Brontë'
    assert title == u'Wuthering Heights'

    # comma-separated lastname, firstname
    firstname, lastname, title = ds._parse_author_title("Carroll, Lewis - Alice's Adventures in Wonderland")
    for var in (firstname, lastname, title):
        assert type(var) is unicode
    assert firstname == u'Lewis'
    assert lastname == u'Carroll'
    assert title == u"Alice's Adventures in Wonderland"

    # comma-separated lastname, firstname & double-barrelled firstname
    firstname, lastname, title = ds._parse_author_title("Andersen, H. C. - Andersen's Fairy Tales")
    for var in (firstname, lastname, title):
        assert type(var) is unicode
    assert firstname == u'H. C.'
    assert lastname == u'Andersen'
    assert title == u"Andersen's Fairy Tales"
