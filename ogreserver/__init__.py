# import Flask library
from flask import Flask
#from ogreserver.blueprint import bp
#from werkzeug.contrib.fixers import ProxyFix

# import Flask extensions
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager
from flask.ext.uploads import UploadSet, ALL, configure_uploads
#from flask.ext.script import Manager
#from flask.ext.cache import Cache

# setup Celery
from ogreserver.celery import celery

# import python core libraries
#import os, json
#from datetime import datetime

# import AWS interface
#import boto

# instantiate Flask application
app = Flask(__name__)
app.config.from_pyfile("config/flask.app.conf.py")
#app.register_blueprint(bp)

# setup SQLAlchemy
db = SQLAlchemy(app)

# memcache config
#cache = Cache(app)

# setup Flask-Login
login_manager = LoginManager()
login_manager.setup_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(userid):
    from ogreserver.models.user import User
    user = User.query.filter_by(id=int(userid)).first()
    return user

# setup Flask-Upload
uploads = UploadSet('ebooks', ALL)
configure_uploads(app, (uploads))

# import ogreserver
import ogreserver.views
import ogreserver.tasks

# HACK to support dev
for rule in app.url_map.iter_rules():
    rule.rule = "/ogre" + rule.rule
    rule.refresh()
