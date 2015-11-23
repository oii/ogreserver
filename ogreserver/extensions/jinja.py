from __future__ import absolute_import
from __future__ import unicode_literals

import babel.dates


def init_jinja(app):
    @app.template_filter('date')
    def format_date(value, fmt='medium'):
        return babel.dates.format_date(value, fmt, locale='en')
