from __future__ import absolute_import
from __future__ import unicode_literals

from flask.ext.wtf import Form
from wtforms import TextField, BooleanField


class SearchForm(Form):
    s = TextField('s')
    is_curated = BooleanField('Curated Only?', default=True)
    is_fiction = BooleanField('Fiction Only?', default=True)
