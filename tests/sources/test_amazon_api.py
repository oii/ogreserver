from __future__ import absolute_import
from __future__ import unicode_literals

import mock

from ogreserver import exceptions
from ogreserver.sources.amazon import AmazonAPI

import fixtures


@mock.patch('ogreserver.sources.amazon.bottlenose.Amazon')
def test_author_title_search_no_matches(mock_amazon):
    """
    Validate AmazonAPI class runs three searches before failing on a dodgy author/title
    """
    amazon = AmazonAPI(None, None, None)

    # mock AmazonAPI responses
    mock_amazon.return_value.ItemSearch.side_effect = [
        fixtures.AMAZON_TEST_AUTHOR_TITLE_SEARCH_NO_MATCHES_ITEMSEARCH_NOMATCH,
        fixtures.AMAZON_TEST_AUTHOR_TITLE_SEARCH_NO_MATCHES_ITEMSEARCH_NOMATCH,
        fixtures.AMAZON_TEST_AUTHOR_TITLE_SEARCH_NO_MATCHES_ITEMSEARCH_RESULT,
    ]

    # search author, title on Amazon
    am_data = amazon.search(author='ccc ccc', title='Lee, Harper--To Kill a Mockingbird')
    assert am_data is None
    assert mock_amazon.return_value.ItemSearch.call_count == 3


@mock.patch('ogreserver.sources.amazon.bottlenose.Amazon')
def test_author_title_search_success(mock_amazon):
    """
    Validate AmazonAPI finds author/title first time
    """
    amazon = AmazonAPI(None, None, None)

    # mock AmazonAPI responses
    mock_amazon.return_value.ItemSearch.return_value = fixtures.AMAZON_TEST_AUTHOR_TITLE_SEARCH_SUCCESS_ITEMSEARCH
    mock_amazon.return_value.ItemLookup.return_value = fixtures.AMAZON_TEST_AUTHOR_TITLE_SEARCH_SUCCESS_ITEMLOOKUP

    am_data = amazon.search(author='Richard Morgan', title='Black Man')
    assert mock_amazon.return_value.ItemSearch.call_count == 1
    assert am_data['asin'] == 'B002U3CBZ2'
    assert am_data['author'] == 'Richard Morgan'
    assert am_data['title'] == 'Black Man (GOLLANCZ S.F.)'
    assert am_data['image_url'] == 'https://images-eu.ssl-images-amazon.com/images/I/51fy9mqeVTL.jpg'
    assert am_data['url'] == 'https://www.amazon.co.uk/Black-GOLLANCZ-S-F-Richard-Morgan-ebook/dp/B002U3CBZ2?SubscriptionId=egg&tag=o02a-21&linkCode=xm2&camp=2025&creative=165953&creativeASIN=B002U3CBZ2'


@mock.patch('ogreserver.sources.amazon.bottlenose.Amazon')
def test_invalid_asin_search(mock_amazon):
    """
    Search for a Kindle ASIN, which will raise AmazonItemNotAccessibleError
    Verify a subsequent search for author/title
    """
    amazon = AmazonAPI(None, None, None)

    # mock AmazonAPI responses
    mock_amazon.return_value.ItemLookup.side_effect = [
        exceptions.AmazonItemNotAccessibleError,
        fixtures.AMAZON_TEST_AUTHOR_TITLE_SEARCH_SUCCESS_ITEMLOOKUP
    ]
    mock_amazon.return_value.ItemSearch.return_value = fixtures.AMAZON_TEST_AUTHOR_TITLE_SEARCH_SUCCESS_ITEMSEARCH

    am_data = amazon.search(asin='B003WE9TU8', author='Richard Morgan', title='Black Man')
    assert mock_amazon.return_value.ItemLookup.call_count == 2
    assert am_data['asin'] == 'B002U3CBZ2'
    assert am_data['author'] == 'Richard Morgan'
    assert am_data['title'] == 'Black Man (GOLLANCZ S.F.)'
    assert am_data['image_url'] == 'https://images-eu.ssl-images-amazon.com/images/I/51fy9mqeVTL.jpg'
    assert am_data['url'] == 'https://www.amazon.co.uk/Black-GOLLANCZ-S-F-Richard-Morgan-ebook/dp/B002U3CBZ2?SubscriptionId=egg&tag=o02a-21&linkCode=xm2&camp=2025&creative=165953&creativeASIN=B002U3CBZ2'


@mock.patch('ogreserver.sources.amazon.bottlenose.Amazon')
def test_valid_asin_search(mock_amazon):
    """
    Search for a valid ASIN
    """
    amazon = AmazonAPI(None, None, None)

    # mock AmazonAPI responses
    mock_amazon.return_value.ItemLookup.side_effect = [
        fixtures.AMAZON_TEST_AUTHOR_TITLE_SEARCH_SUCCESS_ITEMSEARCH,
        fixtures.AMAZON_TEST_AUTHOR_TITLE_SEARCH_SUCCESS_ITEMLOOKUP
    ]

    am_data = amazon.search(asin='B002U3CBZ2', author='Richard Morgan', title='Black Man')
    assert mock_amazon.return_value.ItemLookup.call_count == 2
    assert am_data['asin'] == 'B002U3CBZ2'
    assert am_data['author'] == 'Richard Morgan'
    assert am_data['title'] == 'Black Man (GOLLANCZ S.F.)'
    assert am_data['image_url'] == 'https://images-eu.ssl-images-amazon.com/images/I/51fy9mqeVTL.jpg'
    assert am_data['url'] == 'https://www.amazon.co.uk/Black-GOLLANCZ-S-F-Richard-Morgan-ebook/dp/B002U3CBZ2?SubscriptionId=egg&tag=o02a-21&linkCode=xm2&camp=2025&creative=165953&creativeASIN=B002U3CBZ2'


@mock.patch('ogreserver.sources.amazon.bottlenose.Amazon')
def test_author_title_unicode(mock_amazon):
    """
    Ensure the results from AmazonAPI are unicode type
    """
    amazon = AmazonAPI(None, None, None)

    # mock AmazonAPI responses
    mock_amazon.return_value.ItemSearch.return_value = fixtures.AMAZON_TEST_AUTHOR_TITLE_SEARCH_SUCCESS_ITEMSEARCH
    mock_amazon.return_value.ItemLookup.return_value = fixtures.AMAZON_TEST_AUTHOR_TITLE_SEARCH_SUCCESS_ITEMLOOKUP

    am_data = amazon.search(author='Richard Morgan', title='Black Man')
    assert type(am_data['asin']) is unicode
    assert type(am_data['author']) is unicode
    assert type(am_data['title']) is unicode
    assert type(am_data['image_url']) is unicode
    assert type(am_data['url']) is unicode
