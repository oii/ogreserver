from __future__ import absolute_import
from __future__ import unicode_literals

from flask import jsonify

from ogreserver.models.ebook import Ebook, Version, Format
from ogreserver.stores import ebooks as ebook_store


def test_ebook_json_serializable(postgresql, user, ebook_fixture_azw3):
    # create test ebook data
    ebook_store.create_ebook(
        "Andersen's Fairy Tales", 'H. C. Andersen', user, ebook_fixture_azw3
    )

    assert jsonify(Ebook.query.first())


def test_version_json_serializable(postgresql, user, ebook_fixture_azw3):
    # create test ebook data
    ebook_store.create_ebook(
        "Andersen's Fairy Tales", 'H. C. Andersen', user, ebook_fixture_azw3
    )

    assert jsonify(Version.query.first())


def test_format_json_serializable(postgresql, user, ebook_fixture_azw3):
    # create test ebook data
    ebook_store.create_ebook(
        "Andersen's Fairy Tales", 'H. C. Andersen', user, ebook_fixture_azw3
    )

    assert jsonify(Format.query.first())
