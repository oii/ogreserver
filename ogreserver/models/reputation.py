from __future__ import absolute_import
from __future__ import unicode_literals

from sqlalchemy import Column, Integer, Boolean, ForeignKey

from flask import g
from flask import current_app as app

from .ebook import SyncEvent
from ..extensions.database import Base


class Badges:
    Beta_Tester, Fastidious, Contributor, Scholar, Librarian, Pirate, Keener = range(1,8)


class Reputation():

    def __init__(self, user):
        self.user = user

    def new_ebooks(self, count):
        """
        Each new book uploaded earns a user a point
        """
        self.user.points += count
        g.db_session.add(self.user)
        g.db_session.commit()

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
        Check if a user has earned any badges on this sync
        """
        stats = None

        if not self.user.has_badge(Badges.Beta_Tester):
            # everyone who uses the app during beta phase gets this badge
            if app.config['BETA'] is True:
                self.award(Badges.Beta_Tester)

        if not self.user.has_badge(Badges.Fastidious):
            # not sure what this badge means yet
            pass

        if not self.user.has_badge(Badges.Keener):
            # user ran a sync 10 times with nothing new to report
            count = SyncEvent.query.distinct(
                SyncEvent.user_id, SyncEvent.syncd_books_count
            ).count()

            if count >= 10:
                self.award(Badges.Keener)

        if not self.user.has_badge(Badges.Librarian):
            # award badges for volume uploads
            if not stats:
                stats = self.user.get_stats()

            if stats['total_uploads'] >= 200:
                self.award(Badges.Librarian)
            elif stats['total_uploads'] >= 100:
                self.award(Badges.Scholar)
            elif stats['total_uploads'] >= 20:
                self.award(Badges.Contributor)

        if not self.user.has_badge(Badges.Pirate):
            # award badge for decrypted ebooks
            if not stats:
                stats = self.user.get_stats()

            elif stats['total_dedrm'] > 0:
                self.award(Badges.Pirate)


    def award(self, badge):
        """
        Award a badge to a user in the DB
        """
        if Reputation.has_badge(self.user, badge):
            return
        ub = UserBadge(user_id=self.user.id, badge=badge)
        g.db_session.add(ub)
        g.db_session.commit()

    @staticmethod
    def has_badge(user, badge):
        """
        Check if a user has a certain badge
        """
        return next((True for b in user.badges if b.badge == badge), False)


class UserBadge(Base):
    __tablename__ = 'user_badge'

    user_id = Column(Integer, ForeignKey('user.id'), primary_key=True)
    badge = Column(Integer, primary_key=True, autoincrement=False)
    been_alerted = Column(Boolean, default=False)

    def __str__(self):
        if self.badge == Badges.Beta_Tester:
            return "You earned the Beta Tester badge. Thanks for the help spod."
        elif self.badge == Badges.Fastidious:
            return "You earned the Fastidious badge."
        elif self.badge == Badges.Contributor:
            return "You earned the Contributor badge. Over 20 books uploaded."
        elif self.badge == Badges.Scholar:
            return "You earned the Scholar badge. Over 100 books uploaded."
        elif self.badge == Badges.Librarian:
            return "You earned the Librarian badge. Over 200 books uploaded."
        elif self.badge == Badges.Pirate:
            return "You earned the Pirate badge. First DRM cleansed upload."
        elif self.badge == Badges.Keener:
            return "You earned the Keener badge. Ten syncs with nothing to show!"

    def set_alerted(self):
        """
        Flag that the has been alerted about earning this badge
        """
        self.been_alerted = True
        g.db_session.add(self)
        g.db_session.commit()
