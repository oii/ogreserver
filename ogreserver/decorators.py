from __future__ import absolute_import
from __future__ import unicode_literals

import functools
import urllib2

from flask import current_app as app, request
from werkzeug.exceptions import Forbidden

from .exceptions import APIAccessDenied


def handle_http_error(excp):
    """
    Capture urllib2.HTTPError and instead raise the `excp` passed to the decorator.

    In the case of a 403, raise APIAccessDenied with `excp` as the inner_exception.
    """
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


def slack_token_required(f):
    @functools.wraps(f)
    def wrapped(*args, **kwargs):
        if app.config['SLACK_TOKEN'] == request.form.get('token'):
            return f(*args, **kwargs)
        else:
            raise Forbidden
    return wrapped
