from ogreserver import app, db

from ogreserver.models.log import Log

from sqlalchemy import exc
from sqlalchemy.sql import func


class Badges:
    Beta_Tester, Fastidious, Contributor, Scholar, Librarian, Pirate = range(1,7)


class Reputation():

    def __init__(self, user):
        self.user = user

    def new_ebooks(self, count):
        self.user.points += count
        db.session.add(self.user)
        db.session.commit()

    def get_new_badges(self):
        new_badges = UserBadge.query.filter_by(user_id=self.user.id, been_alerted=False)
        msgs = []

        for b in new_badges:
            msgs.append(str(b))
            b.set_alerted()

        return msgs

    def earn_badges(self):
        if self.user.has_badge(Badges.Beta_Tester) == False:
            if app.config['BETA'] == True:
                self.award(Badges.Beta_Tester)

        if self.user.has_badge(Badges.Fastidious) == False:
            # TODO test this theory
            logs = Log.query.filter_by(user_id=self.user.id, type="NEW", data=0).all()

        if self.user.has_badge(Badges.Librarian) == False:
            count = db.session.query(func.count(Log.id)).filter_by(user_id=self.user.id, type="UPLOAD").scalar()

            if count > 200:
                self.award(Badges.Librarian)
            elif count > 100:
                self.award(Badges.Scholar)
            elif count > 20:
                self.award(Badges.Contributor)

        if self.user.has_badge(Badges.Pirate) == False:
            # TODO work out how to check for DRM removal
            self.award(Badges.Pirate)

    def award(self, badge):
        try:
            ub = UserBadge(user_id=self.user.id, badge=badge)
            db.session.add(ub)
            db.session.commit()
        except exc.IntegrityError:
            pass


class UserBadge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    badge = db.Column(db.Integer)
    been_alerted = db.Column(db.Boolean, default=False)

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
        self.been_alerted = True
        db.session.add(self)
        db.session.commit()

