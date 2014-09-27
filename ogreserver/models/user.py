from __future__ import absolute_import

import datetime

from flask.ext.login import UserMixin

import rethinkdb as r

from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .security import pwd_context
from .reputation import Reputation, UserBadge

from flask import current_app as app

from ..extensions.database import Base, get_db


class User(Base, UserMixin):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    username = Column(String(80))
    password = Column(String(256))
    email = Column(String(120), unique=True)
    display_name = Column(String(50), unique=True)
    api_key_expires = Column(DateTime)
    points = Column(Integer, default=0)
    needs_password_reset = Column(Boolean, default=1)
    preferred_ebook_format = Column(String(4))
    dont_email_me = Column(Boolean, default=False)
    badges = relationship(UserBadge, backref='user', lazy='dynamic')
    total_users = None
    session_api_key = None

    def __init__(self, username, password, email):
        self.username = username
        self.password = pwd_context.encrypt(password)
        self.email = email

    def save(self):
        db_session = get_db(app)
        db_session.add(self)
        db_session.commit()

    @staticmethod
    def authenticate(username, password):
        """
        Authenticate a user by username and password
        """
        user = User.query.filter_by(username=username).first()
        if not user:
            return None
        elif pwd_context.verify(password, user.password) is False:
            return None
        return user

    @staticmethod
    def _compile_pre_key(username, password, timestamp):
        return "%s:%s:%s:%s" % (app.config['SECRET_KEY'], username, password, timestamp)

    @staticmethod
    def create_auth_key(username, password, timestamp):
        """
        Construct a unique identifier for an API key by encrypting output from _compile_pre_key()
        """
        return pwd_context.encrypt(User._compile_pre_key(username, password, timestamp))

    @staticmethod
    def validate_auth_key(username, api_key):
        """
        Validate an incoming API key
        """
        # load the user by name
        user = User.query.filter_by(username=username).first()
        if not user:
            return None

        # TODO check API key hasn't expired

        # reconstruct the key and verify it
        prekey = User._compile_pre_key(user.username, user.password, user.api_key_expires)
        if pwd_context.verify(prekey, api_key) == True:
            user.session_api_key = api_key
            return user
        else:
            return None

    def assign_auth_key(self):
        """
        Generate a new API key and save against the user
        """
        self.api_key_expires = datetime.datetime.utcnow()
        self.api_key_expires = self.api_key_expires.replace(microsecond=0)    # remove microseconds for mysql
        api_key = User.create_auth_key(self.username, self.password, self.api_key_expires)
        db_session = get_db(app)
        db_session.add(self)
        db_session.commit()
        return "%s+%s" % (self.username, api_key)

    # Flask-Login method
    def is_authenticated(self):
        """
        Check user is authenticated
        """
        if self.email is not None:
            return True
        else:
            return False

    def has_badge(self, badge):
        """
        Check if this user has earnt a specific badge
        """
        return Reputation.has_badge(self, badge)

    def get_stats(self):
        conn = r.connect("localhost", 28015, db=app.config['RETHINKDB_DATABASE'])

        # get the number of times user has sync'd
        total_syncs = r.table('sync_events').get_all(
            self.username, index='username'
        ).count().run(conn)

        # total uploads
        total_uploads = r.table('formats').get_all(
            [self.username, True], index='user_uploads'
        ).count().run(conn)

        # number of DRM cleaned books
        total_dedrm = r.table('formats').get_all(
            [self.username, True], index='user_dedrm'
        ).count().run(conn)

        return {
            'total_syncs': total_syncs,
            'total_uploads': total_uploads,
            'total_dedrm': total_dedrm,
        }

    @staticmethod
    def get_total_users():
        """
        Return the total number of registered users
        """
        if User.total_users is None:
            db_session = get_db(app)
            q = db_session.query(func.count(User.id))
            User.total_users = db_session.execute(q).scalar()
        return User.total_users

    def __str__(self):
        return "<User: %s, %s>" % (self.id, self.username)
