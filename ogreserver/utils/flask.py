from __future__ import absolute_import
from __future__ import unicode_literals

from flask import render_template as flask_render_template

from ..forms.search import SearchForm


def request_wants_json(request):
    best = request.accept_mimetypes.best_match(['application/json', 'text/html'])
    return best == 'application/json' and \
        request.accept_mimetypes[best] > \
        request.accept_mimetypes['text/html']


def render_template(template, **context):
    '''
    Wrap Flask's render_template() function to add SearchForm() to every rendered template
    '''
    if 'search_form' not in context:
        context['search_form'] = SearchForm(csrf_enabled=False)
    return flask_render_template(template, **context)
