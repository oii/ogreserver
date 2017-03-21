from __future__ import absolute_import
from __future__ import unicode_literals

from flask_security import UserMixin, RoleMixin
from flask_security import utils as security_utils

from sqlalchemy import Table, Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship, backref

from .ebook import Format, SyncEvent
from .reputation import Reputation, UserBadge
from ..extensions.database import Base

from flask import g


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


class classproperty(property):
    def __get__(self, cls, owner):
        return classmethod(self.fget).__get__(None, owner)()


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
    needs_password_reset = Column(Boolean, default=True)
    preferred_ebook_format = Column(String(4))
    dont_email_me = Column(Boolean, default=False)
    badges = relationship(UserBadge, backref='user', lazy='dynamic')
    advanced = Column(Boolean)

    active = Column(Boolean)
    confirmed_at = Column(DateTime)
    last_login_at = Column(DateTime)
    current_login_at = Column(DateTime)
    last_login_ip = Column(String(15))
    current_login_ip = Column(String(15))
    login_count = Column(Integer)

    total_users = None
    _ogrebot = None

    def __init__(self, username, password, email, active, roles):
        self.username = username
        self.password = security_utils.encrypt_password(password)
        self.email = email
        self.active = active
        self.roles = roles

    def save(self):
        g.db_session.add(self)
        g.db_session.commit()

    def has_badge(self, badge):
        """
        Check if this user has earnt a specific badge
        """
        return Reputation.has_badge(self, badge)

    def get_stats(self):
        # get the number of times user has sync'd
        total_syncs = SyncEvent.query.distinct(SyncEvent.user_id).count()

        # total uploads
        total_uploads = Format.query.filter(
            Format.uploader == self,
            Format.uploaded == True
        ).count()

        # number of DRM cleaned books
        total_dedrm = Format.query.filter(
            Format.uploader == self,
            Format.uploaded == True,
            Format.dedrm == True
        ).count()

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
            User.total_users = User.query.distinct().count()
        return User.total_users

    @classproperty
    def ogrebot(cls):
        """
        Return the OGRE internal user
        """
        if cls._ogrebot is None:
            cls._ogrebot = User.query.filter_by(username='ogrebot').first()
        return cls._ogrebot

    def __str__(self):
        return "<User: %s, %s>" % (self.id, self.username)
