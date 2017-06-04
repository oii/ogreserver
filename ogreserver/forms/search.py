from __future__ import absolute_import
from __future__ import unicode_literals

from flask_wtf import FlaskForm
from wtforms import TextField, BooleanField


class SearchForm(FlaskForm):
    s = TextField('s')
    is_curated = BooleanField('Curated Only?', default=True)
    is_fiction = BooleanField('Fiction Only?', default=True)
