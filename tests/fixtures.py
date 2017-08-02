from __future__ import unicode_literals

import datetime


EBOOK_FIXTURE_1 = {
    'dedrm': True,
    'format': 'azw3',
    'file_hash': '6c9376c4b8834df00ede127014c6efce',
    'meta': {
        'publisher': u"O'Reilly Media",
        'isbn': '9781491999999',
        'firstname': 'H. C.',
        'tags': '',
        'lastname': 'Andersen',
        'title': "Andersen's Fairy Tales",
        'source': 'Amazon Kindle',
        'publish_date': '2014-09-05T07:00:00+00:00',
        'asin': 'B00KG6MZ2O'
    },
    'size': 10877312
}

EBOOK_FIXTURE_2 = {
    'dedrm': False,
    'format': 'pdf',
    'file_hash': 'e9cafe2cc658e198310239c03a0d390b',
    'meta': {
        'publisher': 'Egg Publishing',
        'isbn': '9781491990000',
        'firstname': 'Eggbert',
        'tags': '',
        'lastname': 'Yolker',
        'title': 'The Sun is an Egg',
        'source': 'Unknown',
        'publish_date': '2013-07-05T07:00:00+00:00',
        'asin': 'B00KG6ZZZZ'
    },
    'size': 973355
}

EBOOK_FIXTURE_3 = {
    'dedrm': False,
    'format': 'epub',
    'file_hash': '5c253944f52d9bf3114611687a372eb0',
    'meta': {
        'publisher': 'Bantam',
        'isbn': '86739271908',
        'firstname': 'Issac',
        'tags': '',
        'lastname': 'Asimov',
        'title': 'Foundation',
        'source': 'Unknown',
        'publish_date': '2016-07-08T13:30:00+00:00',
        'asin': 'B00KF5AAAZ'
    },
    'size': 746218
}


AMAZON_TEST_AUTHOR_TITLE_SEARCH_NO_MATCHES_ITEMSEARCH_NOMATCH = """<?xml version="1.0" ?>
<ItemSearchResponse xmlns="http://webservices.amazon.com/AWSECommerceService/2013-08-01">
    <OperationRequest>
        <HTTPHeaders>
            <Header Name="UserAgent" Value="Python-urllib/2.7" />
        </HTTPHeaders>
        <RequestId>025b6728-cf2c-4648-aaf0-852ef927cc53</RequestId>
        <Arguments>
            <Argument Name="AWSAccessKeyId" Value="egg" />
            <Argument Name="AssociateTag" Value="o02a-21" />
            <Argument Name="Keywords" Value="ccc ccc Lee, Harper--To Kill a Mockingbird" />
            <Argument Name="Operation" Value="ItemSearch" />
            <Argument Name="SearchIndex" Value="KindleStore" />
            <Argument Name="Service" Value="AWSECommerceService" />
            <Argument Name="Timestamp" Value="2017-08-01T15:53:06Z" />
            <Argument Name="Version" Value="2013-08-01" />
            <Argument Name="Signature" Value="ZOcThowp45jkL0GmiXVotkdy0hAQzZfXJVj/DztvneE=" />
        </Arguments>
        <RequestProcessingTime>0.0140179890000000</RequestProcessingTime>
    </OperationRequest>
    <Items>
        <Request>
            <IsValid>True</IsValid>
            <ItemSearchRequest>
                <Keywords>ccc ccc Lee, Harper--To Kill a Mockingbird</Keywords>
                <ResponseGroup>Small</ResponseGroup>
                <SearchIndex>KindleStore</SearchIndex>
            </ItemSearchRequest>
            <Errors>
                <Error>
                    <Code>AWS.ECommerceService.NoExactMatches</Code>
                    <Message>We did not find any matches for your request.</Message>
                </Error>
            </Errors>
        </Request>
        <TotalResults>0</TotalResults>
        <TotalPages>0</TotalPages>
        <MoreSearchResultsUrl>https://www.amazon.co.uk/gp/search?linkCode=xm2&amp;SubscriptionId=egg&amp;keywords=ccc%20ccc%20Lee%2C%20Harper--To%20Kill%20a%20Mockingbird&amp;tag=o02a-21&amp;creative=12734&amp;url=search-alias%3Ddigital-text&amp;camp=2025</MoreSearchResultsUrl>
    </Items>
</ItemSearchResponse>
"""

AMAZON_TEST_AUTHOR_TITLE_SEARCH_NO_MATCHES_ITEMSEARCH_RESULT = """<?xml version="1.0" ?>
<ItemSearchResponse xmlns="http://webservices.amazon.com/AWSECommerceService/2013-08-01">
    <OperationRequest>
        <HTTPHeaders>
            <Header Name="UserAgent" Value="Python-urllib/2.7" />
        </HTTPHeaders>
        <RequestId>cd0d696c-2e9f-4a0f-ad82-6bdf4ea4ea4d</RequestId>
        <Arguments>
            <Argument Name="AWSAccessKeyId" Value="egg" />
            <Argument Name="AssociateTag" Value="o02a-21" />
            <Argument Name="Keywords" Value="ccc ccc Lee, Harper--To Kill a Mockingbird" />
            <Argument Name="Operation" Value="ItemSearch" />
            <Argument Name="SearchIndex" Value="Books" />
            <Argument Name="Service" Value="AWSECommerceService" />
            <Argument Name="Timestamp" Value="2017-08-01T15:53:35Z" />
            <Argument Name="Version" Value="2013-08-01" />
            <Argument Name="Signature" Value="ME7bg8w/xzn74REy6+hSdhX2Et9HKUyUitsQJ0hSjZg=" />
        </Arguments>
        <RequestProcessingTime>0.0278894580000000</RequestProcessingTime>
    </OperationRequest>
    <Items>
        <Request>
            <IsValid>True</IsValid>
            <ItemSearchRequest>
                <Keywords>ccc ccc Lee, Harper--To Kill a Mockingbird</Keywords>
                <ResponseGroup>Small</ResponseGroup>
                <SearchIndex>Books</SearchIndex>
            </ItemSearchRequest>
            <Errors>
                <Error>
                    <Code>AWS.ECommerceService.NoExactMatches</Code>
                    <Message>We did not find any matches for your request.</Message>
                </Error>
            </Errors>
        </Request>
        <TotalResults>0</TotalResults>
        <TotalPages>0</TotalPages>
        <MoreSearchResultsUrl>https://www.amazon.co.uk/gp/search?linkCode=xm2&amp;SubscriptionId=egg&amp;keywords=ccc%20ccc%20Lee%2C%20Harper--To%20Kill%20a%20Mockingbird&amp;tag=o02a-21&amp;creative=12734&amp;url=search-alias%3Dbooks-single-index&amp;camp=2025</MoreSearchResultsUrl>
    </Items>
</ItemSearchResponse>
"""

AMAZON_TEST_AUTHOR_TITLE_SEARCH_SUCCESS_ITEMSEARCH = """<?xml version="1.0" ?>
<ItemSearchResponse xmlns="http://webservices.amazon.com/AWSECommerceService/2013-08-01">
    <OperationRequest>
        <HTTPHeaders>
            <Header Name="UserAgent" Value="Python-urllib/2.7" />
        </HTTPHeaders>
        <RequestId>6fad145d-dd7a-4bcd-97e7-9fd020f3299b</RequestId>
        <Arguments>
            <Argument Name="AWSAccessKeyId" Value="egg" />
            <Argument Name="AssociateTag" Value="o02a-21" />
            <Argument Name="Keywords" Value="Richard Morgan Black Man" />
            <Argument Name="Operation" Value="ItemSearch" />
            <Argument Name="SearchIndex" Value="KindleStore" />
            <Argument Name="Service" Value="AWSECommerceService" />
            <Argument Name="Timestamp" Value="2017-08-02T06:25:14Z" />
            <Argument Name="Version" Value="2013-08-01" />
            <Argument Name="Signature" Value="MefQx5fchD4G5mpSakKQuUvVZcq2YJipUob4jv5qFqw=" />
        </Arguments>
        <RequestProcessingTime>0.0240643290000000</RequestProcessingTime>
    </OperationRequest>
    <Items>
        <Request>
            <IsValid>True</IsValid>
            <ItemSearchRequest>
                <Keywords>Richard Morgan Black Man</Keywords>
                <ResponseGroup>Small</ResponseGroup>
                <SearchIndex>KindleStore</SearchIndex>
            </ItemSearchRequest>
        </Request>
        <TotalResults>2</TotalResults>
        <TotalPages>1</TotalPages>
        <MoreSearchResultsUrl>https://www.amazon.co.uk/gp/search?linkCode=xm2&amp;SubscriptionId=egg&amp;keywords=Richard%20Morgan%20Black%20Man&amp;tag=o02a-21&amp;creative=12734&amp;url=search-alias%3Ddigital-text&amp;camp=2025</MoreSearchResultsUrl>
        <Item>
            <ASIN>B002U3CBZ2</ASIN>
            <DetailPageURL>https://www.amazon.co.uk/Black-GOLLANCZ-S-F-Richard-Morgan-ebook/dp/B002U3CBZ2?SubscriptionId=egg&amp;tag=o02a-21&amp;linkCode=xm2&amp;camp=2025&amp;creative=165953&amp;creativeASIN=B002U3CBZ2</DetailPageURL>
            <ItemLinks>
                <ItemLink>
                    <Description>Add To Wishlist</Description>
                    <URL>https://www.amazon.co.uk/gp/registry/wishlist/add-item.html?asin.0=B002U3CBZ2&amp;SubscriptionId=egg&amp;tag=o02a-21&amp;linkCode=xm2&amp;camp=2025&amp;creative=12734&amp;creativeASIN=B002U3CBZ2</URL>
                </ItemLink>
                <ItemLink>
                    <Description>Tell A Friend</Description>
                    <URL>https://www.amazon.co.uk/gp/pdp/taf/B002U3CBZ2?SubscriptionId=egg&amp;tag=o02a-21&amp;linkCode=xm2&amp;camp=2025&amp;creative=12734&amp;creativeASIN=B002U3CBZ2</URL>
                </ItemLink>
                <ItemLink>
                    <Description>All Customer Reviews</Description>
                    <URL>https://www.amazon.co.uk/review/product/B002U3CBZ2?SubscriptionId=egg&amp;tag=o02a-21&amp;linkCode=xm2&amp;camp=2025&amp;creative=12734&amp;creativeASIN=B002U3CBZ2</URL>
                </ItemLink>
                <ItemLink>
                    <Description>All Offers</Description>
                    <URL>https://www.amazon.co.uk/gp/offer-listing/B002U3CBZ2?SubscriptionId=egg&amp;tag=o02a-21&amp;linkCode=xm2&amp;camp=2025&amp;creative=12734&amp;creativeASIN=B002U3CBZ2</URL>
                </ItemLink>
            </ItemLinks>
            <ItemAttributes>
                <Author>Richard Morgan</Author>
                <Manufacturer>Gollancz</Manufacturer>
                <ProductGroup>eBooks</ProductGroup>
                <Title>Black Man (GOLLANCZ S.F.)</Title>
            </ItemAttributes>
        </Item>
        <Item>
            <ASIN>B005PR0Y4A</ASIN>
            <DetailPageURL>https://www.amazon.co.uk/Black-SCIENCE-FICTION-French-Richard-Morgan-ebook/dp/B005PR0Y4A?SubscriptionId=egg&amp;tag=o02a-21&amp;linkCode=xm2&amp;camp=2025&amp;creative=165953&amp;creativeASIN=B005PR0Y4A</DetailPageURL>
            <ItemLinks>
                <ItemLink>
                    <Description>Add To Wishlist</Description>
                    <URL>https://www.amazon.co.uk/gp/registry/wishlist/add-item.html?asin.0=B005PR0Y4A&amp;SubscriptionId=egg&amp;tag=o02a-21&amp;linkCode=xm2&amp;camp=2025&amp;creative=12734&amp;creativeASIN=B005PR0Y4A</URL>
                </ItemLink>
                <ItemLink>
                    <Description>Tell A Friend</Description>
                    <URL>https://www.amazon.co.uk/gp/pdp/taf/B005PR0Y4A?SubscriptionId=egg&amp;tag=o02a-21&amp;linkCode=xm2&amp;camp=2025&amp;creative=12734&amp;creativeASIN=B005PR0Y4A</URL>
                </ItemLink>
                <ItemLink>
                    <Description>All Customer Reviews</Description>
                    <URL>https://www.amazon.co.uk/review/product/B005PR0Y4A?SubscriptionId=egg&amp;tag=o02a-21&amp;linkCode=xm2&amp;camp=2025&amp;creative=12734&amp;creativeASIN=B005PR0Y4A</URL>
                </ItemLink>
                <ItemLink>
                    <Description>All Offers</Description>
                    <URL>https://www.amazon.co.uk/gp/offer-listing/B005PR0Y4A?SubscriptionId=egg&amp;tag=o02a-21&amp;linkCode=xm2&amp;camp=2025&amp;creative=12734&amp;creativeASIN=B005PR0Y4A</URL>
                </ItemLink>
            </ItemLinks>
            <ItemAttributes>
                <Author>Richard Morgan</Author>
                <Manufacturer>Milady</Manufacturer>
                <ProductGroup>eBooks</ProductGroup>
                <Title>Black Man (SCIENCE-FICTION) (French Edition)</Title>
            </ItemAttributes>
        </Item>
    </Items>
</ItemSearchResponse>
"""

AMAZON_TEST_AUTHOR_TITLE_SEARCH_SUCCESS_ITEMLOOKUP = """<?xml version="1.0" ?>
<ItemLookupResponse xmlns="http://webservices.amazon.com/AWSECommerceService/2013-08-01">
    <OperationRequest>
        <HTTPHeaders>
            <Header Name="UserAgent" Value="Python-urllib/2.7" />
        </HTTPHeaders>
        <RequestId>65d55c6c-19f7-4dc1-b6cb-578f2583f525</RequestId>
        <Arguments>
            <Argument Name="AWSAccessKeyId" Value="egg" />
            <Argument Name="AssociateTag" Value="o02a-21" />
            <Argument Name="ItemId" Value="B002U3CBZ2" />
            <Argument Name="Operation" Value="ItemLookup" />
            <Argument Name="ResponseGroup" Value="Images" />
            <Argument Name="Service" Value="AWSECommerceService" />
            <Argument Name="Timestamp" Value="2017-08-02T06:29:46Z" />
            <Argument Name="Version" Value="2013-08-01" />
            <Argument Name="Signature" Value="0geD4slhwt8YTRCvyO8D90Mi9Yxj16L5JoHCI8zwXNM=" />
        </Arguments>
        <RequestProcessingTime>0.0038972700000000</RequestProcessingTime>
    </OperationRequest>
    <Items>
        <Request>
            <IsValid>True</IsValid>
            <ItemLookupRequest>
                <IdType>ASIN</IdType>
                <ItemId>B002U3CBZ2</ItemId>
                <ResponseGroup>Images</ResponseGroup>
                <VariationPage>All</VariationPage>
            </ItemLookupRequest>
        </Request>
        <Item>
            <ASIN>B002U3CBZ2</ASIN>
            <SmallImage>
                <URL>https://images-eu.ssl-images-amazon.com/images/I/51fy9mqeVTL._SL75_.jpg</URL>
                <Height Units="pixels">75</Height>
                <Width Units="pixels">49</Width>
            </SmallImage>
            <MediumImage>
                <URL>https://images-eu.ssl-images-amazon.com/images/I/51fy9mqeVTL._SL160_.jpg</URL>
                <Height Units="pixels">160</Height>
                <Width Units="pixels">104</Width>
            </MediumImage>
            <LargeImage>
                <URL>https://images-eu.ssl-images-amazon.com/images/I/51fy9mqeVTL.jpg</URL>
                <Height Units="pixels">500</Height>
                <Width Units="pixels">325</Width>
            </LargeImage>
            <ImageSets>
                <ImageSet Category="primary">
                    <SwatchImage>
                        <URL>https://images-eu.ssl-images-amazon.com/images/I/51fy9mqeVTL._SL30_.jpg</URL>
                        <Height Units="pixels">30</Height>
                        <Width Units="pixels">20</Width>
                    </SwatchImage>
                    <SmallImage>
                        <URL>https://images-eu.ssl-images-amazon.com/images/I/51fy9mqeVTL._SL75_.jpg</URL>
                        <Height Units="pixels">75</Height>
                        <Width Units="pixels">49</Width>
                    </SmallImage>
                    <ThumbnailImage>
                        <URL>https://images-eu.ssl-images-amazon.com/images/I/51fy9mqeVTL._SL75_.jpg</URL>
                        <Height Units="pixels">75</Height>
                        <Width Units="pixels">49</Width>
                    </ThumbnailImage>
                    <TinyImage>
                        <URL>https://images-eu.ssl-images-amazon.com/images/I/51fy9mqeVTL._SL110_.jpg</URL>
                        <Height Units="pixels">110</Height>
                        <Width Units="pixels">72</Width>
                    </TinyImage>
                    <MediumImage>
                        <URL>https://images-eu.ssl-images-amazon.com/images/I/51fy9mqeVTL._SL160_.jpg</URL>
                        <Height Units="pixels">160</Height>
                        <Width Units="pixels">104</Width>
                    </MediumImage>
                    <LargeImage>
                        <URL>https://images-eu.ssl-images-amazon.com/images/I/51fy9mqeVTL.jpg</URL>
                        <Height Units="pixels">500</Height>
                        <Width Units="pixels">325</Width>
                    </LargeImage>
                    <HiResImage>
                        <URL>https://images-eu.ssl-images-amazon.com/images/I/81qwu-NBfiL.jpg</URL>
                        <Height Units="pixels">2560</Height>
                        <Width Units="pixels">1663</Width>
                    </HiResImage>
                </ImageSet>
            </ImageSets>
        </Item>
    </Items>
</ItemLookupResponse>
"""

AMAZON_TEST_VALID_ASIN_SEARCH_ITEMSEARCH = """<?xml version="1.0" ?>
<ItemLookupResponse xmlns="http://webservices.amazon.com/AWSECommerceService/2013-08-01">
    <OperationRequest>
        <HTTPHeaders>
            <Header Name="UserAgent" Value="Python-urllib/2.7" />
        </HTTPHeaders>
        <RequestId>607ba22a-bc18-496b-a71c-ffd49a422588</RequestId>
        <Arguments>
            <Argument Name="AWSAccessKeyId" Value="egg" />
            <Argument Name="AssociateTag" Value="egg" />
            <Argument Name="ItemId" Value="B003WE9TU8" />
            <Argument Name="Operation" Value="ItemLookup" />
            <Argument Name="Service" Value="AWSECommerceService" />
            <Argument Name="Timestamp" Value="2015-10-20T16:00:10Z" />
            <Argument Name="Version" Value="2013-08-01" />
            <Argument Name="Signature" Value="CKINO9FqjN7j2y4KNovWDs4I3lyEvG2xht4vgDtwbBg=" />
        </Arguments>
        <RequestProcessingTime>0.0094890000000000</RequestProcessingTime>
    </OperationRequest>
    <Items>
        <Request>
            <IsValid>True</IsValid>
            <ItemLookupRequest>
                <IdType>ASIN</IdType>
                <ItemId>B003WE9TU8</ItemId>
                <ResponseGroup>Small</ResponseGroup>
                <VariationPage>All</VariationPage>
            </ItemLookupRequest>
            <Errors>
                <Error>
                    <Code>AWS.ECommerceService.ItemNotAccessible</Code>
                    <Message>This item is not accessible through the Product Advertising API.</Message>
                </Error>
            </Errors>
        </Request>
    </Items>
</ItemLookupResponse>
"""


GOODREADS_BOOK_DATA_0307346609 = {
    'asin': None,
    'isbn': '0307346609',
    'description': 'The Zombie War came unthinkably close to eradicating humanity.',
    'isbn13': '9780307346605',
    'title': 'World War Z: An Oral History of the Zombie War',
    'publisher': 'Crown',
    'average_rating': '4.01',
    'authors': [5791],
    'image_url': 'https://images.gr-assets.com/books/1386328204m/8908.jpg',
    'publication_date': datetime.date(2006, 9, 12),
    'link': 'https://www.goodreads.com/book/show/8908.World_War_Z',
    'num_pages': '342'
}

GOODREADS_AUTHOR_DATA_0307346609 = {
    'born_at': None,
    'hometown': 'New York City',
    'small_image_url': 'https://images.gr-assets.com/authors/1334340170p2/5791.jpg',
    'name': 'Max Brooks',
    'died_at': None
}

GOODREADS_BOOK_DATA_MORGAN_ALTERED_CARBON = {
    'asin': None,
    'isbn': '0345457692',
    'description': 'It\'s the twenty-fifth century, and advances in technology have redefined life itself.',
    'isbn13': '9780345457691',
    'title': 'Altered Carbon (Takeshi Kovacs, #1)',
    'publisher': 'Del Rey Books',
    'average_rating': '4.10',
    'authors': [16496],
    'image_url': 'https://images.gr-assets.com/books/1387128955m/40445.jpg',
    'publication_date': datetime.date(2006, 2, 28),
    'link': 'https://www.goodreads.com/book/show/40445.Altered_Carbon',
    'num_pages': '526'
}

GOODREADS_AUTHOR_DATA_MORGAN_ALTERED_CARBON = {
    'born_at': '1965/09/24',
    'hometown': 'London, England',
    'small_image_url': 'https://images.gr-assets.com/authors/1175224722p2/16496.jpg',
    'name': 'Richard K. Morgan',
    'died_at': None
}

GOODREADS_BOOK_QUERY_8908 = """<?xml version="1.0" encoding="UTF-8"?>
<GoodreadsResponse>
    <Request>
        <authentication>true</authentication>
        <key><![CDATA[nEJqQiErsyBDPudiOYovmA]]></key>
        <method><![CDATA[book_show]]></method>
    </Request>
    <book>
        <id>8908</id>
        <title><![CDATA[World War Z: An Oral History of the Zombie War]]></title>
        <isbn><![CDATA[0307346609]]></isbn>
        <isbn13><![CDATA[9780307346605]]></isbn13>
        <asin />
        <kindle_asin><![CDATA[B00YLR2FW4]]></kindle_asin>
        <marketplace_id><![CDATA[A1F83G8C2ARO7P]]></marketplace_id>
        <country_code><![CDATA[GB]]></country_code>
        <image_url>https://images.gr-assets.com/books/1386328204m/8908.jpg</image_url>
        <small_image_url>https://images.gr-assets.com/books/1386328204s/8908.jpg</small_image_url>
        <publication_year>2006</publication_year>
        <publication_month>9</publication_month>
        <publication_day>12</publication_day>
        <publisher>Crown</publisher>
        <language_code>en-US</language_code>
        <is_ebook>false</is_ebook>
        <description><![CDATA[The Zombie War came unthinkably close to eradicating humanity.]]></description>
        <work>
            <id type="integer">817</id>
            <books_count type="integer">135</books_count>
            <best_book_id type="integer">8908</best_book_id>
            <reviews_count type="integer">551208</reviews_count>
            <ratings_sum type="integer">1376532</ratings_sum>
            <ratings_count type="integer">343616</ratings_count>
            <text_reviews_count type="integer">22356</text_reviews_count>
            <original_publication_year type="integer">2006</original_publication_year>
            <original_publication_month type="integer" nil="true" />
            <original_publication_day type="integer" nil="true" />
            <original_title>World War Z: An Oral History of the Zombie War</original_title>
            <original_language_id type="integer" nil="true" />
            <media_type>book</media_type>
            <rating_dist>5:129860|4:121064|3:65243|2:19798|1:7651|total:343616</rating_dist>
            <desc_user_id type="integer">2830758</desc_user_id>
            <default_chaptering_book_id type="integer" nil="true" />
            <default_description_language_code nil="true" />
        </work>
        <average_rating>4.01</average_rating>
        <num_pages><![CDATA[342]]></num_pages>
        <format><![CDATA[Hardcover]]></format>
        <edition_information />
        <ratings_count><![CDATA[311616]]></ratings_count>
        <text_reviews_count><![CDATA[18958]]></text_reviews_count>
        <url><![CDATA[https://www.goodreads.com/book/show/8908.World_War_Z]]></url>
        <link><![CDATA[https://www.goodreads.com/book/show/8908.World_War_Z]]></link>
        <authors>
            <author>
                <id>5791</id>
                <name>Max Brooks</name>
                <role />
                <image_url nophoto="false">
<![CDATA[https://images.gr-assets.com/authors/1334340170p5/5791.jpg]]>
</image_url>
                <small_image_url nophoto="false">
<![CDATA[https://images.gr-assets.com/authors/1334340170p2/5791.jpg]]>
</small_image_url>
                <link><![CDATA[https://www.goodreads.com/author/show/5791.Max_Brooks]]></link>
                <average_rating>3.97</average_rating>
                <ratings_count>449486</ratings_count>
                <text_reviews_count>27394</text_reviews_count>
            </author>
        </authors>
        <reviews_widget>
      <![CDATA[
        <style>
  #goodreads-widget {
    font-family: georgia, serif;
    padding: 18px 0;
    width:565px;
  }
  #goodreads-widget h1 {
    font-weight:normal;
    font-size: 16px;
    border-bottom: 1px solid #BBB596;
    margin-bottom: 0;
  }
  #goodreads-widget a {
    text-decoration: none;
    color:#660;
  }
  iframe{
    background-color: #fff;
  }
  #goodreads-widget a:hover { text-decoration: underline; }
  #goodreads-widget a:active {
    color:#660;
  }
  #gr_footer {
    width: 100%;
    border-top: 1px solid #BBB596;
    text-align: right;
  }
  #goodreads-widget .gr_branding{
    color: #382110;
    font-size: 11px;
    text-decoration: none;
    font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
  }
</style>
<div id="goodreads-widget">
  <div id="gr_header"><h1><a rel="nofollow" href="https://www.goodreads.com/book/show/8908.World_War_Z">World War Z Reviews</a></h1></div>
  <iframe id="the_iframe" src="https://www.goodreads.com/api/reviews_widget_iframe?did=DEVELOPER_ID&amp;format=html&amp;isbn=0307346609&amp;links=660&amp;min_rating=&amp;review_back=fff&amp;stars=000&amp;text=000" width="565" height="400" frameborder="0"></iframe>
  <div id="gr_footer">
    <a class="gr_branding" target="_blank" rel="nofollow" href="https://www.goodreads.com/book/show/8908.World_War_Z?utm_medium=api&amp;utm_source=reviews_widget">Reviews from Goodreads.com</a>
  </div>
</div>

      ]]>
    </reviews_widget>
        <popular_shelves>
            <shelf name="to-read" count="31064" />
        </popular_shelves>
        <book_links>
            <book_link>
                <id>8</id>
                <name>Libraries</name>
                <link>https://www.goodreads.com/book_link/follow/8</link>
            </book_link>
        </book_links>
        <buy_links>
            <buy_link>
                <id>1</id>
                <name>Amazon</name>
                <link>https://www.goodreads.com/book_link/follow/1</link>
            </buy_link>
        </buy_links>
        <series_works />
        <public_document>
            <id>19575</id>
            <document_url>
          https://s3.amazonaws.com/compressed.photo.goodreads.com/documents/1331146541books/8908.pdf
        </document_url>
        </public_document>
        <similar_books>
            <book>
                <id>8429687</id>
                <title><![CDATA[Deadline (Newsflesh Trilogy, #2)]]></title>
                <title_without_series>Deadline</title_without_series>
                <link><![CDATA[https://www.goodreads.com/book/show/8429687-deadline]]></link>
                <small_image_url><![CDATA[https://images.gr-assets.com/books/1408500444s/8429687.jpg]]></small_image_url>
                <image_url><![CDATA[https://images.gr-assets.com/books/1408500444m/8429687.jpg]]></image_url>
                <num_pages>584</num_pages>
                <work>
                    <id>13292985</id>
                </work>
                <isbn>031608106X</isbn>
                <isbn13>9780316081061</isbn13>
                <average_rating>4.10</average_rating>
                <ratings_count>20108</ratings_count>
                <publication_year>2011</publication_year>
                <publication_month>6</publication_month>
                <publication_day>1</publication_day>
                <authors>
                    <author>
                        <id>3153776</id>
                        <name>Mira Grant</name>
                        <link><![CDATA[https://www.goodreads.com/author/show/3153776.Mira_Grant]]></link>
                    </author>
                </authors>
            </book>
            <book>
                <id>1085771</id>
                <title><![CDATA[The Walking Dead, Vol. 07: The Calm Before]]></title>
                <title_without_series><![CDATA[The Walking Dead, Vol. 07: The Calm Before]]></title_without_series>
                <link><![CDATA[https://www.goodreads.com/book/show/1085771.The_Walking_Dead_Vol_07]]></link>
                <small_image_url><![CDATA[https://images.gr-assets.com/books/1289097173s/1085771.jpg]]></small_image_url>
                <image_url><![CDATA[https://images.gr-assets.com/books/1289097173m/1085771.jpg]]></image_url>
                <num_pages>136</num_pages>
                <work>
                    <id>1072542</id>
                </work>
                <isbn>1582408289</isbn>
                <isbn13>9781582408286</isbn13>
                <average_rating>4.27</average_rating>
                <ratings_count>17464</ratings_count>
                <publication_year>2010</publication_year>
                <publication_month>11</publication_month>
                <publication_day>9</publication_day>
                <authors>
                    <author>
                        <id>12425</id>
                        <name>Robert Kirkman</name>
                        <link><![CDATA[https://www.goodreads.com/author/show/12425.Robert_Kirkman]]></link>
                    </author>
                </authors>
            </book>
        </similar_books>
    </book>
</GoodreadsResponse>
"""
