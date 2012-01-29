# import Flask library
from flask import Flask
#from werkzeug.contrib.fixers import ProxyFix

# import Flask extensions
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager
from flask.ext.celery import Celery

# import python core libraries
import os, json
from datetime import datetime

# import AWS interface
import boto

# instantiate Flask application
app = Flask(__name__)
app.config.from_pyfile("config/config.py")

# setup SQLAlchemy
db = SQLAlchemy(app)

# setup Celery interface
celery = Celery(app)

# import ogreserver
import ogreserver.models
import ogreserver.views
import ogreserver.tasks

# setup Flask-Login
login_manager = LoginManager()
login_manager.setup_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(userid):
    user = models.User.query.filter_by(id=int(userid)).first()
    return user


