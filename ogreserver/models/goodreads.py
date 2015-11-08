from __future__ import absolute_import
from __future__ import unicode_literals

import datetime

import requests
import xml.etree.cElementTree as ET

from ..exceptions import GoodreadsAPIError, GoodreadsBookNotFoundError
from ..utils import clean_string, handle_http_error


class GoodreadsAPI:
    def __init__(self, logger, api_key):
        self.logger = logger
        self.api_key = api_key


    def _query(self, method, querystr):
        params = {'key': self.api_key, 'format': 'xml'}

        # if search method, pass 'q' on querystring,
        # otherwise include as part of the URL
        if method == 'search':
            params.update({'q': querystr})
        else:
            method = '{}/{}'.format(method, querystr)

        # query the API
        resp = requests.get(
            'https://www.goodreads.com/{}'.format(method), params=params
        )

        # error handle
        if resp.status_code == 404:
            raise GoodreadsBookNotFoundError
        elif resp.status_code != 200:
            raise GoodreadsAPIError('{} returned from {}'.format(resp.status_code, method))

        # more non-standardised API balls from Goodreads
        if method.startswith('book/isbn_to_id'):
            return resp.text

        # parse xml
        tree = ET.fromstring(resp.text.encode('utf-8'))

        # check results count on search
        if method == 'search':
            try:
                if int(tree.find('search').find('total-results').text) == 0:
                    raise GoodreadsBookNotFoundError
            except (AttributeError, ValueError):
                raise GoodreadsAPIError("Couldn't get results count: {} {}".format(method, querystr))

        return tree


    @handle_http_error(GoodreadsAPIError)
    def search(self, author=None, title=None, isbn=None, retry=0):
        if isbn is not None:
            try:
                book_id = self._query('book/isbn_to_id', isbn)

            except GoodreadsBookNotFoundError:
                # tidy up the author/title fields and try again
                return self.search(
                    author=clean_string(author), title=clean_string(title), retry=retry+1
                )
        else:
            try:
                # query Goodreads
                tree = self._query('search', '{} {}'.format(author or '', title or ''))

                # extract first result from Goodread's search
                book = tree.find('search').find('results').findall('work')[0].find('best_book')
                book_id = int(book.find('id').text)

            except ValueError:
                raise GoodreadsAPIError(
                    'Failed parsing book_id: title={}, author={}, isbn={}'.format(title, author, isbn)
                )
            except GoodreadsBookNotFoundError:
                if retry > 1:
                    return None

                # tidy up the author/title fields and try again
                return self.search(
                    author=clean_string(author), title=clean_string(title), retry=retry+1
                )

        output = {}

        # retrieve further detailed info from Goodreads
        book_data = self.get_book(book_id)
        output.update(book_data)

        output['authors'] = []

        # extract the author ids
        for author_id in book_data['authors']:
            author_data = self.get_author(author_id)
            output['authors'].append(author_data)

        # convert everything to unicode
        for k,v in output.items():
            if type(v) is str:
                output[k] = v.decode('utf8')

        return output


    def _try_field(self, obj, field_name):
        try:
            return obj.find(field_name).text
        except AttributeError:
            pass


    def get_book(self, book_id):
        xml = self._query('book/show', book_id)
        book = xml.find('book')

        output = {}

        # extract the interesting bits
        for key in ('isbn', 'isbn13', 'asin', 'image_url', 'publisher', 'title', \
                    'description', 'average_rating', 'num_pages', 'link'):
            output[key] = self._try_field(book, key)

        # extract publication date
        year = self._try_field(book, 'original_publication_year')
        if not year:
            year = self._try_field(book, 'publication_year')

        if year:
            month = self._try_field(book, 'original_publication_month')
            if not month:
                month = self._try_field(book, 'publication_month')
            if not month:
                # default January
                month = 1

            day = self._try_field(book, 'original_publication_day')
            if not day:
                day = self._try_field(book, 'publication_day')
            if not day:
                # default first of the day
                day = 1

            output['publication_date'] = datetime.date(
                int(year), int(month), int(day)
            )

        # extract list of authors
        output['authors'] = []

        for author in book.find('authors'):
            output['authors'].append(int(author.find('id').text))

        return output


    def get_author(self, author_id):
        xml = self._query('author/show', author_id)
        author = xml.find('author')

        output = {}

        for key in ('name', 'small_image_url', 'hometown', 'born_at', 'died_at'):
            # Goodreads likes double spaces
            item = self._try_field(author, key)
            if item:
                item = item.replace('  ', ' ')
            output[key] = item

        return output
