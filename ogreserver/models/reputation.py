from __future__ import absolute_import

from sqlalchemy import Column, Integer, Boolean, ForeignKey
from sqlalchemy.sql import func

from .. import app
from ..database import Base, db_session
from .log import Log


class Badges:
    Beta_Tester, Fastidious, Contributor, Scholar, Librarian, Pirate = range(1,7)


class Reputation():

    def __init__(self, user):
        self.user = user

    def new_ebooks(self, count):
        """
        Each new book uploaded earns a user a point
        """
        self.user.points += count
        db_session.add(self.user)
        db_session.commit()

    def get_new_badges(self):
        """
        Retrieve badges this user hasn't been alerted about
        """
        new_badges = UserBadge.query.filter_by(user_id=self.user.id, been_alerted=False)
        msgs = []

        for b in new_badges:
            msgs.append(str(b))
            b.set_alerted()

        return msgs

    def earn_badges(self):
        """
        Check if a user has earned any badges on this synchronisation
        """
        if self.user.has_badge(Badges.Beta_Tester) == False:
            if app.config['BETA'] == True:
                self.award(Badges.Beta_Tester)

        if self.user.has_badge(Badges.Fastidious) == False:
            # TODO test this theory
            logs = Log.query.filter_by(user_id=self.user.id, type="NEW", data=0).all()

        if self.user.has_badge(Badges.Librarian) == False:
            count = db_session.query(func.count(Log.id)).filter_by(user_id=self.user.id, type="STORED").scalar()

            if count > 200:
                self.award(Badges.Librarian)
            elif Reputation.has_badge(self.user, Badges.Scholar) == False and count > 100:
                self.award(Badges.Scholar)
            elif Reputation.has_badge(self.user, Badges.Contributor) == False and count > 20:
                self.award(Badges.Contributor)

        if Reputation.has_badge(self.user, Badges.Pirate) == False:
            if Log.query.filter_by(user_id=self.user.id, type="DEDRM", data=1).first() is not None:
                self.award(Badges.Pirate)

    def award(self, badge):
        """
        Award a badge to a user in the DB
        """
        ub = UserBadge(user_id=self.user.id, badge=badge)
        db_session.add(ub)
        db_session.commit()

    @staticmethod
    def has_badge(user, badge):
        """
        Check if a user has a certain badge
        """
        for b in user.badges:
            if b.badge == badge:
                return True
        return False


class UserBadge(Base):
    __tablename__ = 'user_badge'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    badge = Column(Integer)
    been_alerted = Column(Boolean, default=False)

    def __str__(self):
        if self.badge == Badges.Beta_Tester:
            return "You earned the 'Beta Tester' badge. Thanks for the help spod."
        elif self.badge == Badges.Fastidious:
            return "You earned the 'Fastidious' badge. Nothing to upload th== time!"
        elif self.badge == Badges.Contributor:
            return "You earned the 'Contributor' badge. Over 20 books uploaded."
        elif self.badge == Badges.Scholar:
            return "You earned the 'Scholar' badge. Over 100 books uploaded."
        elif self.badge == Badges.Librarian:
            return "You earned the 'Librarian' badge. Over 200 books uploaded."
        elif self.badge == Badges.Pirate:
            return "You earned the 'Pirate' badge. First DRM cleansed upload."

    def set_alerted(self):
        """
        Flag that the has been alerted about earning this badge
        """
        self.been_alerted = True
        db_session.add(self)
        db_session.commit()
