from __future__ import unicode_literals


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
