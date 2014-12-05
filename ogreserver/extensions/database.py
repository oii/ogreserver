from __future__ import absolute_import

from flask import g

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


def get_db(app):
    if not hasattr(g, 'db_session'):
        engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'], convert_unicode=True)
        g.db_session = scoped_session(sessionmaker(autocommit=False,
                                                   autoflush=False,
                                                   bind=engine))
        Base.query = g.db_session.query_property()

    return g.db_session


def shutdown_db_session(exception=None):
    if hasattr(g, 'db_session'):
        g.db_session.remove()


def create_tables(app):
    # import all modules here that define models
    from ..models.reputation import UserBadge
    from ..models.user import User, Role, roles_users

    # create the DB tables
    engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'], convert_unicode=True)
    Base.metadata.create_all(bind=engine)


def setup_roles(app):
    # create the roles
    from ogreserver.extensions.flask_security import init_security
    app.security = init_security(app)
    app.security.datastore.create_role(name='Admin')
    app.security.datastore.create_role(name='Editor')
    app.security.datastore.create_role(name='User')
    app.security.datastore.commit()
