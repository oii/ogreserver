from __future__ import absolute_import
from __future__ import unicode_literals

import requests
from fuzzywuzzy import process as fuzz
from fuzzywuzzy.fuzz import token_set_ratio

from .. import exceptions


GOOGLE_BOOKS_URL = 'https://www.googleapis.com/books/v1/volumes'


class GoogleBooksAPI:
    def __init__(self, match_threshold=70):
        self.match_threshold = match_threshold


    def _get_single_volume_from_results(self, data, search_str):
        """
        Use fuzzywuzzy to reduce multiple search results down to a single one. Use class attrib
        `match_threshold` to determine valid fuzz matches.

        :params:
            data (list):        list of dicts from Google Books API
            search_str (str):   the author/title string searched for
        """
        if len(data) == 1:
            return data[0]

        choices = {
            '{} {}'.format(' '.join(item['authors']), item['title']):item
            for item in data
        }
        results = fuzz.extract(search_str, choices.keys(), scorer=token_set_ratio)

        # abort if best match is below threshold
        if results[0][1] < self.match_threshold:
            raise exceptions.GoogleNoMatchesError

        # if more than one item shares highest matching rank, roll with first result
        if results[0][1] == results[1][1]:
            match = data[0]
        else:
            # use fuzzywuzzy comparison match
            match = choices[results[0][0]]

        return match


    def search_by_isbn(self, isbn):
        """
        Search Google's Books API for a book by ISBN

        :params:
            isbn (str):     ISBN 11 or 13
        """
        params = {
            'q': 'isbn:{}'.format(isbn),
        }
        return self._search(params)


    def search_by_author_title(self, author, title, retry=0):
        """
        Search Google's Books API for a book by author/title pair

        :params:
            author (str):   Book author
            title (str):    Book title
        """
        params = {
            'q': 'intitle:{}+inauthor:{}'.format(title, author)
        }

        items = self._search(params)

        if len(items) == 1:
            return items[0]

        # extract best match from results
        return self._get_single_volume_from_results(items, '{} {}'.format(author, title))


    def _search(self, params):
        """
        Search Google's Books API with the supplied query parameters

        :params:
            params (str):   Search parameters
        """
        resp = requests.get(GOOGLE_BOOKS_URL, params=params)
        if resp.status_code > 200:
            raise exceptions.GoogleHttpError

        items = []

        for item in resp.json()['items']:
            # subtitle is an optional field - concatenate with title and a colon
            subtitle = ''
            if item['volumeInfo'].get('subtitle'):
                subtitle = ': {}'.format(item['volumeInfo'].get('subtitle', ''))

            items.append({
                'title': '{}{}'.format(item['volumeInfo']['title'], subtitle),
                'authors': item['volumeInfo']['authors'],
                'description': item['volumeInfo'].get('description'),
                'publisher': item['volumeInfo'].get('publisher'),
                'num_pages': item['volumeInfo'].get('pageCount'),
                'link': item['volumeInfo']['canonicalVolumeLink'],
                'image_url': item['volumeInfo']['imageLinks']['thumbnail'],
                'average_rating': item['volumeInfo'].get('averageRating'),
                'categories': item['volumeInfo'].get('categories'),
                'identifiers': {
                    'id': item['id'],
                    'etag': item['etag'],
                }
            })

        return items
