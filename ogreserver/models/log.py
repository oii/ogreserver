from __future__ import absolute_import

import datetime

from sqlalchemy import Column, Integer, String, DateTime

from ..database import Base, db_session



class Log(Base):
    __tablename__ = 'log'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    api_session_key = Column(String(256))
    timestamp = Column(DateTime)  # TODO Log timestamp losing seconds
    type = Column(String(30))
    data = Column(String(200))

    def __init__(self, user_id, api_session_key, type, data):
        self.user_id = user_id
        self.api_session_key = api_session_key
        self.timestamp = datetime.datetime.utcnow()
        self.type = type
        self.data = str(data)

    @staticmethod
    def create(user_id, type, data, api_session_key=None):
        print "%s %s" % (type, data)
        db_session.add(Log(user_id, api_session_key, type, data))
        db_session.commit()
