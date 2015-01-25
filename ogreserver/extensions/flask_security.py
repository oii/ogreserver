from __future__ import absolute_import
from __future__ import unicode_literals

from flask import g

from flask.ext.security import Security, current_user
from flask.ext.security.datastore import Datastore, UserDatastore
from flask.ext.security.forms import LoginForm
from flask.ext.security.signals import password_changed, password_reset, \
        reset_password_instructions_sent, confirm_instructions_sent
from flask.ext.security.utils import get_identity_attributes

from ..models.user import User, Role
from ..signals import when_password_reset, when_password_changed, \
        when_reset_password_sent, when_confirm_instructions_sent


def init_security(app):
    # connect a few signls to trigger emails on events in Flask-Security
    password_reset.connect(when_password_reset, app)
    password_changed.connect(when_password_changed, app)
    reset_password_instructions_sent.connect(when_reset_password_sent, app)
    confirm_instructions_sent.connect(when_confirm_instructions_sent, app)

    # init user storage via Flask-Security
    return Security(app, OgreUserDatastore(app, User, Role), login_form=ExtendedLoginForm)


# disable CSRF for the /login endpoint
class ExtendedLoginForm(LoginForm):
    def __init__(self, *args, **kwargs):
        kwargs['csrf_enabled'] = False
        super(ExtendedLoginForm, self).__init__(*args, **kwargs)


class SQLAlchemyDatastore(Datastore):
    def __init__(self, app):
        self.app = app

    def commit(self):
        g.db_session.commit()

    def put(self, model):
        g.db_session.add(model)
        return model

    def delete(self, model):
        g.db_session.delete(model)


class OgreUserDatastore(SQLAlchemyDatastore, UserDatastore):
    """
    A SQLAlchemy datastore implementation for Flask-Security that assumes the
    use of the Flask-SQLAlchemy extension.
    """
    def __init__(self, app, user_model, role_model):
        SQLAlchemyDatastore.__init__(self, app)
        UserDatastore.__init__(self, user_model, role_model)

    def get_user(self, identifier):
        if self._is_numeric(identifier):
            return self.user_model.query.get(identifier)
        for attr in get_identity_attributes():
            query = getattr(self.user_model, attr).ilike(identifier)
            rv = self.user_model.query.filter(query).first()
            if rv is not None:
                return rv

    def _is_numeric(self, value):
        try:
            int(value)
        except ValueError:
            return False
        return True

    def find_user(self, **kwargs):
        return self.user_model.query.filter_by(**kwargs).first()

    def find_role(self, role):
        return self.role_model.query.filter_by(name=role).first()


def add_user_to_globals():
    # this function is mapped to Flask.before_request() to add the current_user
    # to the Flask request globals
    g.user = current_user
