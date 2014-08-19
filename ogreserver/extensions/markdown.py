from __future__ import absolute_import

# import Flask-Markdown
from flask.ext.markdown import Markdown


def init_markdown(app):
    return Markdown(app)
