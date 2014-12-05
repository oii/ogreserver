from __future__ import absolute_import
from __future__ import unicode_literals

from flask.ext.security import UserMixin, RoleMixin
from flask.ext.security import utils as security_utils

import rethinkdb as r

from sqlalchemy import Table, Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship, backref
from sqlalchemy.sql import func

from .reputation import Reputation, UserBadge

from flask import current_app as app

from ..extensions.database import Base, get_db


roles_users = Table(
    'roles_users', Base.metadata,
    Column('user_id', Integer, ForeignKey('user.id')),
    Column('role_id', Integer, ForeignKey('role.id'))
)

class Role(Base, RoleMixin):
    __tablename__ = 'role'
    id = Column(Integer, primary_key=True)
    name = Column(String(80), unique=True)
    description = Column(String(100))


class User(Base, UserMixin):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True)
    password = Column(String(256))
    email = Column(String(120), unique=True)
    roles = relationship(
        Role, secondary=roles_users, backref=backref('users', lazy='dynamic')
    )
    points = Column(Integer, default=0)
    needs_password_reset = Column(Boolean, default=1)
    preferred_ebook_format = Column(String(4))
    dont_email_me = Column(Boolean, default=False)
    badges = relationship(UserBadge, backref='user', lazy='dynamic')

    active = Column(Boolean)
    confirmed_at = Column(DateTime)
    last_login_at = Column(DateTime)
    current_login_at = Column(DateTime)
    last_login_ip = Column(String(15))
    current_login_ip = Column(String(15))
    login_count = Column(Integer)

    total_users = None

    def __init__(self, username, password, email, active, roles):
        self.username = username
        self.password = security_utils.encrypt_password(password)
        self.email = email
        self.active = active
        self.roles = roles

    def save(self):
        db_session = get_db(app)
        db_session.add(self)
        db_session.commit()

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
