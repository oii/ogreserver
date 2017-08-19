from __future__ import absolute_import
from __future__ import unicode_literals

import mock

from ogreserver.sources.amazon import AmazonAPI


@mock.patch('ogreserver.sources.amazon.bottlenose.Amazon')
def test_author_title_search1(mock_amazon, get_data_fixtures):
    amazon = AmazonAPI(None, None, None)

    # load AmazonAPI response fixtures
    fixtures = get_data_fixtures(__file__, 'test_author_title_search1')
    mock_amazon.return_value.ItemSearch.side_effect = fixtures['mock_amazon_itemsearch']
    mock_amazon.return_value.ItemLookup.side_effect = fixtures['mock_amazon_itemlookup']

    # search author, title on Amazon
    am_data = amazon.search(author='ccc ccc', title='Lee, Harper--To Kill a Mockingbird')
    assert am_data is None


@mock.patch('ogreserver.sources.amazon.bottlenose.Amazon')
def test_author_title_search2(mock_amazon, get_data_fixtures):
    amazon = AmazonAPI(None, None, None)

    # load AmazonAPI response fixtures
    fixtures = get_data_fixtures(__file__, 'test_author_title_search2')
    mock_amazon.return_value.ItemSearch.side_effect = fixtures['mock_amazon_itemsearch']
    mock_amazon.return_value.ItemLookup.side_effect = fixtures['mock_amazon_itemlookup']

    am_data = amazon.search(author='Richard Morgan', title='Black Man')
    assert am_data['asin'] == '2352942322'
    assert am_data['author'] == 'Richard Morgan'
    assert am_data['title'] == 'Black Man'
    assert am_data['image_url'] == 'http://ecx.images-amazon.com/images/I/51URUN95YpL.jpg'
    assert am_data['url'] == 'http://www.amazon.com/Black-Man-Richard-Morgan/dp/2352942322'


@mock.patch('ogreserver.sources.amazon.bottlenose.Amazon')
def test_author_title_search3(mock_amazon, get_data_fixtures):
    amazon = AmazonAPI(None, None, None)

    # load AmazonAPI response fixtures
    fixtures = get_data_fixtures(__file__, 'test_author_title_search3')
    mock_amazon.return_value.ItemSearch.side_effect = fixtures['mock_amazon_itemsearch']
    mock_amazon.return_value.ItemLookup.side_effect = fixtures['mock_amazon_itemlookup']

    am_data = amazon.search(author='Max Brooks', title='World War Z')
    assert am_data['asin'] == 'B000JMKQX0'
    assert am_data['author'] == 'Max Brooks'
    assert am_data['title'] == 'World War Z: An Oral History of the Zombie War'
    assert am_data['image_url'] == 'http://ecx.images-amazon.com/images/I/51ELXqAe9UL.jpg'
    assert am_data['url'] == 'http://www.amazon.com/World-War-Oral-History-Zombie-ebook/dp/B000JMKQX0'


@mock.patch('ogreserver.sources.amazon.bottlenose.Amazon')
def test_author_title_search4(mock_amazon, get_data_fixtures):
    amazon = AmazonAPI(None, None, None)

    # load AmazonAPI response fixtures
    fixtures = get_data_fixtures(__file__, 'test_author_title_search4')
    mock_amazon.return_value.ItemSearch.side_effect = fixtures['mock_amazon_itemsearch']
    mock_amazon.return_value.ItemLookup.side_effect = fixtures['mock_amazon_itemlookup']

    am_data = amazon.search(author='Richard Morgan', title='Altered Carbon (GOLLANCZ S.F.)')
    assert am_data['asin'] == 'B000FBFMZ2'
    assert am_data['author'] == 'Richard K. Morgan'
    assert am_data['title'] == 'Altered Carbon (Takeshi Kovacs Novels Book 1)'
    assert am_data['image_url'] == 'http://ecx.images-amazon.com/images/I/51hFNetqu5L.jpg'
    assert am_data['url'] == 'http://www.amazon.com/Altered-Carbon-Takeshi-Kovacs-Novels-ebook/dp/B000FBFMZ2'


@mock.patch('ogreserver.sources.amazon.bottlenose.Amazon')
def test_invalid_asin_search(mock_amazon, get_data_fixtures):
    amazon = AmazonAPI(None, None, None)

    # load AmazonAPI response fixtures
    fixtures = get_data_fixtures(__file__, 'test_invalid_asin_search')
    mock_amazon.return_value.ItemSearch.side_effect = fixtures['mock_amazon_itemsearch']
    mock_amazon.return_value.ItemLookup.side_effect = fixtures['mock_amazon_itemlookup']

    # search for a Kindle ASIN; which will raise AmazonItemNotAccessibleError
    # and subsequently search by author/title
    am_data = amazon.search(asin='B003WE9TU8', author='Max Brooks', title='World War Z')
    assert am_data['asin'] == 'B000JMKQX0'
    assert am_data['author'] == 'Max Brooks'
    assert am_data['title'] == 'World War Z: An Oral History of the Zombie War'
    assert am_data['image_url'] == 'http://ecx.images-amazon.com/images/I/51ELXqAe9UL.jpg'
    assert am_data['url'] == 'http://www.amazon.com/World-War-Oral-History-Zombie-ebook/dp/B000JMKQX0'


@mock.patch('ogreserver.sources.amazon.bottlenose.Amazon')
def test_valid_asin_search(mock_amazon, get_data_fixtures):
    amazon = AmazonAPI(None, None, None)

    # load AmazonAPI response fixtures
    fixtures = get_data_fixtures(__file__, 'test_valid_asin_search')
    mock_amazon.return_value.ItemSearch.side_effect = fixtures['mock_amazon_itemsearch']
    mock_amazon.return_value.ItemLookup.side_effect = fixtures['mock_amazon_itemlookup']

    # search for a valid ASIN
    am_data = amazon.search(asin='B000JMKQX0')
    assert am_data['asin'] == 'B000JMKQX0'
    assert am_data['author'] == 'Max Brooks'
    assert am_data['title'] == 'World War Z: An Oral History of the Zombie War'
    assert am_data['image_url'] == 'http://ecx.images-amazon.com/images/I/51ELXqAe9UL.jpg'
    assert am_data['url'] == 'http://www.amazon.com/World-War-Oral-History-Zombie-ebook/dp/B000JMKQX0'


@mock.patch('ogreserver.sources.amazon.bottlenose.Amazon')
def test_author_title_unicode(mock_amazon, get_data_fixtures):
    amazon = AmazonAPI(None, None, None)

    # load AmazonAPI response fixtures
    fixtures = get_data_fixtures(__file__, 'test_author_title_search2')
    mock_amazon.return_value.ItemSearch.side_effect = fixtures['mock_amazon_itemsearch']
    mock_amazon.return_value.ItemLookup.side_effect = fixtures['mock_amazon_itemlookup']

    am_data = amazon.search(author='Richard Morgan', title='Black Man')
    assert type(am_data['asin']) is unicode
    assert type(am_data['author']) is unicode
    assert type(am_data['title']) is unicode
    assert type(am_data['image_url']) is unicode
    assert type(am_data['url']) is unicode
