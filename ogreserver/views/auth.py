from __future__ import absolute_import
from __future__ import unicode_literals

import base64

from flask import Blueprint, redirect, request, url_for, render_template
from flask.ext.login import login_required, login_user, logout_user

from werkzeug.exceptions import Forbidden

from ..forms.auth import LoginForm

from ..models.user import User

bp_auth = Blueprint('auth', __name__)


@bp_auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        login_user(form.user)
        return redirect(request.args.get('next') or url_for('core.index'))

    return render_template('login.html', form=form)


@bp_auth.route('/auth', methods=['POST'])
def auth():
    user = User.authenticate(
        username=request.form.get('username'),
        password=request.form.get('password')
    )
    if user == None:
        raise Forbidden
    else:
        return base64.b64encode(user.assign_auth_key())


@bp_auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
