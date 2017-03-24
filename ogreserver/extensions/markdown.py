from __future__ import absolute_import

# import Flask-Markdown
from flask_markdown import Markdown


def init_markdown(app):
    return Markdown(app)
