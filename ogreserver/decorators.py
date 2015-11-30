from __future__ import absolute_import
from __future__ import unicode_literals

import functools
import urllib2

from .exceptions import APIAccessDenied


def handle_http_error(excp):
    def decorator(f):
        @functools.wraps(f)
        def wrapped(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except urllib2.HTTPError as e:
                if e.code == 403:
                    raise APIAccessDenied(inner_excp=excp())
                raise excp
        return wrapped
    return decorator
