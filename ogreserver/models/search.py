from __future__ import absolute_import
from __future__ import unicode_literals

import math

from whoosh.query import Every
from whoosh.qparser import MultifieldParser, OrGroup, FuzzyTermPlugin


class Search:
    def __init__(self, whoosh, pagelen):
        self.whoosh = whoosh
        self.pagelen = pagelen


    def index_for_search(self, ebook_data):
        if self.whoosh is None:
            return

        # add info about this book to the search index
        with self.whoosh.writer() as writer:
            writer.update_document(
                ebook_id=ebook_data['ebook_id'],
                author=ebook_data['author'],
                title=ebook_data['title'],
            )


    def query(self, terms=None, pagenum=1, allpages=False):
        """
        Search for books using whoosh, or return first page from all
        """
        if self.whoosh is None:
            return

        if terms is None:
            # default to list all authors
            query = Every('author')
        else:
            # create a search by author and title
            qp = MultifieldParser(['author', 'title'], self.whoosh.schema, group=OrGroup)

            # fuzzy query only if wildcard not present
            if '*' not in terms:
                qp.add_plugin(FuzzyTermPlugin())

                # setup search terms for fuzzy match
                fuzzy_terms = []
                for w in terms.split():
                    fuzzy_terms.append('{}~'.format(w))
                s = ' '.join(fuzzy_terms)

            # parse the search terms
            query = qp.parse(s)

        output = []
        pagecount = None

        with self.whoosh.searcher() as s:
            if allpages:
                # special search returning all pages upto pagenum
                results = s.search(query, limit=(self.pagelen * pagenum))
            else:
                # paginated search for specific page, or to feed infinite scroll
                results = s.search_page(query, int(pagenum), pagelen=self.pagelen)
                pagecount = results.pagecount

            for item in results:
                output.append(item.fields())

            if pagecount is None:
                pagecount = int(math.ceil(float(len(output)) / self.pagelen))

        return {'results': output, 'pagecount': pagecount}
