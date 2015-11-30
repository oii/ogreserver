from __future__ import absolute_import
from __future__ import unicode_literals

from flask.ext.wtf import Form
from wtforms import TextField


class SearchForm(Form):
    s = TextField('s')
