from __future__ import absolute_import

from flask import g

from flask import Blueprint, render_template
from flask.ext.login import login_required

from .ebooks import listing

bp_core = Blueprint('core', __name__, static_folder='../static')


# declare some error handler pages
@bp_core.app_errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

@bp_core.app_errorhandler(500)
def internal_error(error):
    g.db_session.rollback()
    return render_template('500.html'), 500


@bp_core.route('/')
@login_required
def index():
    return listing()
