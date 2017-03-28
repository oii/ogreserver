from __future__ import absolute_import
from __future__ import unicode_literals

from ogreserver.stores import ebooks as ebook_store


def test_user_uploads_stat(postgresql, user, ebook_db_fixture_azw3, ebook_db_fixture_epub):
    """
    Validate num uploads stat works correctly.
    """
    stats = user.get_stats()
    assert stats['total_uploads'] == 0

    # mark first as uploaded
    ebook_store.set_uploaded(
        ebook_db_fixture_azw3.versions[0].source_format.file_hash, user, filename='egg.pub'
    )

    stats = user.get_stats()
    assert stats['total_uploads'] == 1


def test_user_dedrm_stat(postgresql, user, ebook_fixture_azw3, ebook_fixture_epub):
    """
    Validate DeDRM stat works correctly. AZW3 fixture has dedrm=False.
    """
    # create test ebook data - this is dedrm=False
    ebook_store.create_ebook(
        'Foundation', 'Issac Asimov', user, ebook_fixture_epub
    )
    # mark as uploaded
    ebook_store.set_uploaded(ebook_fixture_epub['file_hash'], user, filename='egg1.pub')

    stats = user.get_stats()
    assert stats['total_dedrm'] == 0

    # create second test ebook - this is dedrm=True
    ebook_store.create_ebook(
        "Andersen's Fairy Tales", 'H. C. Andersen', user, ebook_fixture_azw3
    )
    # mark as uploaded
    ebook_store.set_uploaded(ebook_fixture_azw3['file_hash'], user, filename='egg.pub')

    stats = user.get_stats()
    assert stats['total_dedrm'] == 1
