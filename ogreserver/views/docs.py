from __future__ import absolute_import
from __future__ import unicode_literals

import fileinput
import fnmatch
import os

from flask import Blueprint, abort, render_template, render_template_string
from flask.ext.security.decorators import login_required

bp_docs = Blueprint('docs', __name__)


TEMPLATE_MD_START = (
    '{% extends "layout.html" %}'
    '{% block body %}'
    '{% filter markdown %}'
)
IMPROVE_URL = '\n[Improve this page](https://github.com/oii/ogre/blob/develop/ogreserver/docs/{}.md)'
TEMPLATE_MD_END = (
    '{% endfilter %}'
    '{% endblock %}'
)

@bp_docs.route("/docs")
@bp_docs.route("/docs/<path:doco>")
@login_required
def docs(doco=None):
    if doco is None:
        return docs_listing()
    else:
        return view_doc(doco)


def docs_listing():
    # display docs listing
    pages = []

    # TODO some kind of caching

    # iterate all the docs
    files = sorted(os.listdir('ogreserver/docs'))
    for filename in fnmatch.filter(files, '*.md'):
        summary = None
        title = None

        # extract the title/summary from the markdown header
        finput = fileinput.input(os.path.join('ogreserver/docs', filename))
        for line in finput:
            if line == '\n':
                # end of markdown header
                break
            elif line.startswith('Title'):
                title = line[7:]
            elif line.startswith('Summary'):
                summary = line[9:]
        finput.close()

        pages.append({
            'title': title,
            'summary': summary,
            'filename': os.path.splitext(filename)[0],
        })

    return render_template('docs.html', pages=pages)


def view_doc(doco):
    # render a single doc page
    if not os.path.exists('ogreserver/docs/{}.md'.format(doco)):
        abort(404)

    content = []
    in_header = True
    title = None

    # read in a markdown file from the docs
    for line in fileinput.input('ogreserver/docs/{}.md'.format(doco)):
        if in_header:
            # extract title from header
            if line.startswith('Title'):
                title = line[7:]
            elif line == '\n':
                in_header = False
        elif in_header is False:
            content.append(line)

    # add a link to edit/improve this page
    improve_url = IMPROVE_URL.format(doco)

    # render a string for the Flask jinja template engine
    return render_template_string('{}{}=\n\n{}{}{}'.format(
        TEMPLATE_MD_START,
        title,
        ''.join(content),
        improve_url,
        TEMPLATE_MD_END,
    ))
