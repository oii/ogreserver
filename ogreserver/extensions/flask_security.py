from __future__ import absolute_import
from __future__ import unicode_literals

from flask import g

from flask.ext.security import Security, current_user
from flask.ext.security.datastore import Datastore, UserDatastore
from flask.ext.security.forms import LoginForm
from flask.ext.security.utils import get_identity_attributes

from ..extensions.database import get_db
from ..models.user import User, Role


def init_security(app):
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
        db_session = get_db(self.app)
        db_session.commit()

    def put(self, model):
        db_session = get_db(self.app)
        db_session.add(model)
        return model

    def delete(self, model):
        db_session = get_db(self.app)
        db_session.delete(model)


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
    g.user = current_user
