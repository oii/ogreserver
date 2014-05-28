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
    # import all modules here that might define models
    from .models.log import Log
    from .models.reputation import UserBadge
    from .models.user import User

    # create the DB tables
    engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'], convert_unicode=True)
    Base.metadata.create_all(bind=engine)
