from __future__ import absolute_import

import os

from whoosh.index import create_in, open_dir
from whoosh.fields import Schema, ID, TEXT


def init_whoosh(app):
    if os.path.exists(app.config['WHOOSH_BASE']):
        return open_dir(app.config['WHOOSH_BASE'])
    else:
        os.makedirs(app.config['WHOOSH_BASE'])
        schema = Schema(
            ebook_id=ID(stored=True, unique=True),
            author=TEXT(stored=True),
            title=TEXT(stored=True),
        )
        return create_in(app.config['WHOOSH_BASE'], schema)
