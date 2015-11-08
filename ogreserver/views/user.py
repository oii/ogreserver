from __future__ import absolute_import
from __future__ import unicode_literals

from flask import Blueprint, g, request, render_template, redirect

from flask.ext.security.decorators import login_required

from werkzeug.exceptions import Forbidden

from ..forms.profile_edit import ProfileEditForm

from ..models.user import User

bp_user = Blueprint('user', __name__)


@bp_user.route('/profile')
@bp_user.route('/profile/<int:user_id>')
@login_required
def profile(user_id=None):
    # display the current user, or load another user
    if user_id is None:
        user = g.user
    else:
        user = User.query.get(user_id)

    return render_template('profile.html', user=user, stats=user.get_stats())


@bp_user.route('/profile/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def profile_edit(user_id):
    # users can only edit their own profiles (except superuser)
    if g.user.id > 1 and g.user.id != user_id:
        raise Forbidden

    form = ProfileEditForm(request.form, g.user)
    if form.validate_on_submit():
        form.populate_obj(g.user)
        if g.user.preferred_ebook_format == '-':
            g.user.preferred_ebook_format = None
        g.user.save()
        redirect('profile')

    return render_template('profile_edit.html', user=g.user, form=form)
