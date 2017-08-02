from __future__ import absolute_import
from __future__ import unicode_literals

import mock

from ogreserver.sources.goodreads import GoodreadsAPI

import fixtures


def test_isbn_search():
    goodreads = GoodreadsAPI(None)

    # mock the external calls to Goodreads API
    goodreads._get_book_id_by_isbn = mock.Mock()
    goodreads._get_book_id_by_isbn.return_value = 8908
    goodreads._get_book = mock.Mock()
    goodreads._get_book.return_value = fixtures.GOODREADS_BOOK_DATA_0307346609
    goodreads._get_author = mock.Mock()
    goodreads._get_author.return_value = fixtures.GOODREADS_AUTHOR_DATA_0307346609

    # search ISBN on goodreads
    gr_data = goodreads.search(isbn='0307346609')
    assert gr_data['isbn'] == '0307346609'
    assert gr_data['isbn13'] == '9780307346605'
    assert gr_data['title'] == 'World War Z: An Oral History of the Zombie War'
    assert len(gr_data['authors']) == 1
    assert gr_data['authors'][0]['name'] == 'Max Brooks'


def test_author_title_search():
    goodreads = GoodreadsAPI(None)

    # mock the external calls to Goodreads API
    goodreads._get_book_id_by_author_title = mock.Mock()
    goodreads._get_book_id_by_author_title.return_value = 40445
    goodreads._get_book = mock.Mock()
    goodreads._get_book.return_value = fixtures.GOODREADS_BOOK_DATA_MORGAN_ALTERED_CARBON
    goodreads._get_author = mock.Mock()
    goodreads._get_author.return_value = fixtures.GOODREADS_AUTHOR_DATA_MORGAN_ALTERED_CARBON

    # search author, title on goodreads
    gr_data = goodreads.search(author='Richard Morgan', title='Altered Carbon (GOLLANCZ S.F.)')
    assert gr_data['isbn'] == '0345457692'
    assert gr_data['isbn13'] == '9780345457691'
    assert gr_data['title'] == 'Altered Carbon (Takeshi Kovacs, #1)'
    assert len(gr_data['authors']) == 1
    assert gr_data['authors'][0]['name'] == 'Richard K. Morgan'


@mock.patch('ogreserver.sources.goodreads.requests')
def test_get_book(mock_goodreads):
    goodreads = GoodreadsAPI("nEJqQiErsyBDPudiOYovmA")

    mock_goodreads.get.return_value = mock.Mock(status_code=200, text=fixtures.GOODREADS_BOOK_QUERY_8908)

    # search author, title on goodreads
    gr_data = goodreads._get_book(book_id=8908)
    assert type(gr_data['isbn']) is unicode
    assert type(gr_data['isbn13']) is unicode
    assert type(gr_data['title']) is unicode
