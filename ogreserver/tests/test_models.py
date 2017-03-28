from __future__ import absolute_import
from __future__ import unicode_literals

from flask import jsonify

from ogreserver.models.ebook import Ebook, Version, Format


def test_ebook_json_serializable(postgresql, user, ebook_db_fixture_azw3):
    assert jsonify(Ebook.query.first())


def test_version_json_serializable(postgresql, user, ebook_db_fixture_azw3):
    assert jsonify(Version.query.first())


def test_format_json_serializable(postgresql, user, ebook_db_fixture_azw3):
    assert jsonify(Format.query.first())
