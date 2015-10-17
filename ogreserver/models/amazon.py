from __future__ import absolute_import
from __future__ import unicode_literals

import bottlenose
import xml.etree.cElementTree as ET

from fuzzywuzzy import process as fuzz
from fuzzywuzzy.fuzz import token_set_ratio

from ..exceptions import AmazonAPIError, AmazonItemNotAccessibleError, \
        AmazonNoMatchesError, AmazonHttpError
from ..utils import clean_string, handle_http_error


class AmazonAPI:
    NS = 'http://webservices.amazon.com/AWSECommerceService/2011-08-01'

    def __init__(self, logger, access_key, secret_key, associate_tag, match_threshold=50):
        self.logger = logger
        self.match_threshold = match_threshold

        # bottlenose requires str to pass into hmac
        self.amazon = bottlenose.Amazon(
            str(access_key),
            str(secret_key),
            associate_tag,
            MaxQPS=0.9
        )


    def _preprocess(self, xml):
        """
        Helper function to get to the good stuff in response from Amazon API
        """
        tree = ET.fromstring(xml)
        items = tree.find('{{{}}}Items'.format(self.NS))

        # handle errors from the API call
        errors = items.find('{{{}}}Request'.format(self.NS)).find(
            '{{{}}}Errors'.format(self.NS)
        )

        if errors is not None and len(errors.getchildren()) > 0:
            # check request was valid
            request_is_valid = items.find('{{{}}}Request'.format(self.NS)).find(
                '{{{}}}IsValid'.format(self.NS)
            ).text

            if request_is_valid == 'False':
                # extract the error message and raise generic exception
                message = errors.find('{{{}}}Error'.format(self.NS)).find(
                    '{{{}}}Message'.format(self.NS)
                ).text

                raise AmazonAPIError(message)
            else:
                # get the error message code and raise specific exception
                code = errors.find('{{{}}}Error'.format(self.NS)).find(
                    '{{{}}}Code'.format(self.NS)
                ).text

                if code == 'AWS.ECommerceService.ItemNotAccessible':
                    raise AmazonItemNotAccessibleError
                elif code == 'AWS.ECommerceService.NoExactMatches':
                    raise AmazonNoMatchesError

        return items


    def _process_search(self, xml):
        items = self._preprocess(xml)

        # return set of Items objects
        items = map(
            lambda x: self._extract_item(x),
            items.findall('{{{}}}Item'.format(self.NS))
        )
        items[:] = [i for i in items if i is not None]
        if len(items) == 0:
            raise AmazonNoMatchesError
        return items

    def _extract_item(self, item):
        output = {}
        output['asin'] = item.find('{{{}}}ASIN'.format(self.NS)).text
        output['url'] = item.find('{{{}}}DetailPageURL'.format(self.NS)).text
        try:
            # trim off the Amazon affliate querystring (%3F == ?)
            output['url'] = output['url'].split('%3F')[0]
        except:
            pass

        # further interesting bits
        item = item.find('{{{}}}ItemAttributes'.format(self.NS))
        try:
            output['author'] = item.find('{{{}}}Author'.format(self.NS)).text
        except AttributeError:
            return None
        output['title'] = item.find('{{{}}}Title'.format(self.NS)).text
        return output

    def _process_image(self, xml):
        items = self._preprocess(xml)

        # extract a book cover URL
        return items.find(
            '{{{}}}Item'.format(self.NS)
        ).find(
            '{{{}}}LargeImage'.format(self.NS)
        ).find(
            '{{{}}}URL'.format(self.NS)
        ).text


    def _rank_results(self, items, term):
        if len(items) == 1:
            return items[0]

        choices = {'{} {}'.format(item['author'], item['title']):item for item in items}
        results = fuzz.extract(term, choices.keys(), scorer=token_set_ratio)

        if results[0][1] < self.match_threshold:
            raise AmazonNoMatchesError

        # if more than one item shares highest matching rank, roll with Amazon's first result
        if results[0][1] == results[1][1]:
            match = items[0]
        else:
            # use fuzzywuzzy comparison match
            match = choices[results[0][0]]

        # store alternatives for later
        match['alternatives'] = [ (choices[i[0]], i[1]) for i in results if choices[i[0]] != match ]
        return match


    @handle_http_error(AmazonHttpError)
    def search(self, author=None, title=None, asin=None, retry=0, search_index='KindleStore'):
        if asin is not None:
            try:
                # query Amazon and parse XML response
                xml = self.amazon.ItemLookup(ItemId=asin)
                items = self._process_search(xml)

            except (AmazonItemNotAccessibleError, AmazonNoMatchesError):
                # Amazon won't tell us about this item; true for all Kindle ASINs
                return self.search(author=author, title=title)
        else:
            try:
                # query Amazon and parse XML response
                xml = self.amazon.ItemSearch(
                    Keywords='{} {}'.format(author, title),
                    SearchIndex=search_index
                )
                items = self._process_search(xml)

            except AmazonNoMatchesError:
                if retry > 1:
                    return None
                elif retry > 0 and search_index == 'KindleStore':
                    # use the "Books" search index instead
                    search_index = 'Books'

                # tidy up the author/title fields and try again
                return self.search(
                    author=clean_string(author),
                    title=clean_string(title),
                    retry=retry+1,
                    search_index=search_index
                )

        try:
            # use fuzzywuzzy to find best match
            match = self._rank_results(items, '{} {}'.format(author, title))
        except AmazonNoMatchesError:
            return None

        try:
            # query for an image
            xml = self.amazon.ItemLookup(
                ItemId=match['asin'],
                ResponseGroup='Images'
            )
            match['image_url'] = self._process_image(xml)
        except:
            pass
        return match
