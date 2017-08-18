from __future__ import absolute_import
from __future__ import unicode_literals

import mock
import pytest

from ogreserver import exceptions
from ogreserver.sources.google_books import GoogleBooksAPI

import fixtures


def test_search_by_isbn_calls__search():
    gb = GoogleBooksAPI()
    gb._search = mock.MagicMock()
    gb._search.return_value = [None]

    gb.search_by_isbn('0307346609')
    gb._search.assert_called_with({'q': 'isbn:0307346609'})


def test_search_by_author_title_calls__search():
    gb = GoogleBooksAPI()
    gb._search = mock.MagicMock()
    gb._search.return_value = [None]

    gb.search_by_author_title('Richard Morgan', 'The Cold Commands')
    gb._search.assert_called_with({'q': 'intitle:The Cold Commands+inauthor:Richard Morgan'})


@mock.patch('ogreserver.sources.google_books.requests')
def test__search_raises_error_on_non_200(mock_requests):
    gb = GoogleBooksAPI()

    mock_requests.get.return_value = mock.Mock(status_code=202)

    with pytest.raises(exceptions.GoogleHttpError):
        gb._search({'q': 'isbn:0307346609'})


@mock.patch('ogreserver.sources.google_books.requests')
def test__search_produces_valid_dict(mock_requests):
    """
    Validate the contents of the book_data dict returned by _search
    """
    gb = GoogleBooksAPI()

    mock_requests.get.return_value = mock.Mock(status_code=200)
    mock_requests.get.return_value.json.return_value = fixtures.GOOGLE_BOOKS_ISBN_0307346609

    items = gb._search({'q': 'isbn:0307346609'})

    assert items[0]['title'] == 'World War Z: An Oral History of the Zombie War'
    assert items[0]['authors'] == ['Max Brooks']
    assert items[0]['description'] == 'An account of the decade-long conflict between humankind and hordes of the predatory undead.'
    assert items[0]['publisher'] == 'Crown Pub'
    assert items[0]['num_pages'] == 342
    assert items[0]['link'] == 'https://books.google.com/books/about/World_War_Z.html?hl=&id=BW1lAAAAMAAJ'
    assert items[0]['image_url'] == 'http://books.google.com/books/content?id=BW1lAAAAMAAJ&printsec=frontcover&img=1&zoom=1&source=gbs_api'
    assert items[0]['average_rating'] == 3.5
    assert items[0]['categories'] == ['Fiction']
    assert items[0]['identifiers']['id'] == 'BW1lAAAAMAAJ'
    assert items[0]['identifiers']['etag'] == 'JZdiu+0/+7Q'


def test__single_result_gets_single_volume():
    """
    Ensure fuzzywuzzy filtering returns correct match
    """
    gb = GoogleBooksAPI()

    item = gb._get_single_volume_from_results(
        fixtures.GOOGLE_BOOKS__SEARCH_SINGLE_RESULT, 'Richard Morgan The Cold Commands'
    )
    assert item['title'] == 'World War Z: An Oral History of the Zombie War'
    assert item['authors'] == ['Max Brooks']


@mock.patch('ogreserver.sources.google_books.fuzz')
def test__multiple_results_gets_single_volume(mock_fuzz):
    """
    Ensure _get_single_volume_from_results returns first item when there's only a single item
    """
    gb = GoogleBooksAPI()

    item = gb._get_single_volume_from_results(
        fixtures.GOOGLE_BOOKS__SEARCH_MULTIPLE_RESULTS, 'search string is useless in this case'
    )
    assert item['title'] == 'The Dark Defiles'
    assert item['authors'] == ['Richard K. Morgan']
    assert mock_fuzz.called is False
