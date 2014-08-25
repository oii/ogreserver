from __future__ import absolute_import

from flask import g

# import Flask-Login
from flask.ext.login import LoginManager, current_user


def init_login(app):
    login_manager = LoginManager()
    login_manager.setup_app(app)

    @login_manager.user_loader
    def load_user(userid):
        from ogreserver.models.user import User
        user = User.query.get(userid)
        return user

    return login_manager


def add_user_to_globals():
    g.user = current_user
