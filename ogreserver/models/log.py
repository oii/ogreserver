from ogreserver import app, db

from datetime import datetime


class Log(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    api_session_key = db.Column(db.String(256))
    timestamp = db.Column(db.DateTime)  # TODO Log timestamp losing seconds
    type = db.Column(db.String(30))
    data = db.Column(db.String(200))

    def __init__(self, user, api_session_key):
        self.user_id = user.id
        self.api_session_key = api_session_key

    def save(self, type, data):
        print "%s %s" % (type, data)
        self.timestamp = datetime.utcnow()
        self.type = type
        self.data = str(data)
        db.session.add(self)
        db.session.commit()

