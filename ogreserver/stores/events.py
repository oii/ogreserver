from __future__ import absolute_import
from __future__ import unicode_literals

import datetime

from flask import g

from ..models.ebook import SyncEvent


def log(user, syncd_books_count, new_books_count):
    """
    Add entries to a log every time a user syncs from ogreclient
    """
    event = SyncEvent(
        user=user,
        syncd_books_count=syncd_books_count,
        new_books_count=new_books_count,
        timestamp=datetime.datetime.now(),
    )
    g.db_session.add(event)
    g.db_session.commit()
