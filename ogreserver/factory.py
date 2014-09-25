from __future__ import absolute_import

import os

from flask import Flask
from celery import Celery

from .extensions.celery import queue_configuration, schedule_tasks

flask_conf = os.path.join(os.getcwd(), 'flask.app.conf.py')


def create_app(config=None):
    # instantiate Flask application
    app = Flask(__name__)

    if config is not None and type(config) is dict:
        app.config.update(config)
    else:
        try:
            app.config.from_pyfile(flask_conf)
        except IOError:
            raise Exception('Missing application config! No file at {}'.format(flask_conf))

    # import SQLAlchemy disconnect and map to Flask request shutdown
    from .extensions.database import shutdown_db_session
    app.before_request(setup_db_session)
    app.teardown_appcontext(shutdown_db_session)

    # setup application logging
    from .extensions.logging import init_logging
    init_logging(app)

    return app


def make_celery(app):
    # http://flask.pocoo.org/docs/0.10/patterns/celery

    # create Celery app object
    celery = Celery(app.import_name, broker=app.config['BROKER_URL'])

    # load config defined in flask.app.py, queue config & celerybeat schedule
    celery.conf.update(app.config)
    celery.conf.update(queue_configuration())
    celery.conf.update(schedule_tasks())

    TaskBase = celery.Task

    class ContextTask(TaskBase):
        abstract = True
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask

    # register tasks with celery; see extensions/celery.py
    return celery


def configure_extensions(app):
    # init Whoosh for full-text search
    from .extensions.whoosh import init_whoosh
    app.whoosh = init_whoosh(app)

    # setup Flask-Login
    from .extensions.flask_login import init_login, add_user_to_globals
    app.login_manager = init_login(app)
    app.before_request(add_user_to_globals)

    # setup Flask-Uploads
    from .extensions.flask_uploads import init_uploads
    app.uploaded_ebooks, app.uploaded_logs = init_uploads(app)

    # setup Flask-Markdown
    from flaskext.markdown import Markdown
    Markdown(app, extensions=['footnotes'])


def register_blueprints(app):
    # import view blueprints and register with the Flask app
    from .views import bp_core
    from .views.api import bp_api
    from .views.auth import bp_auth
    from .views.docs import bp_docs
    from .views.ebooks import bp_ebooks
    from .views.user import bp_user
    app.register_blueprint(bp_core)
    app.register_blueprint(bp_api)
    app.register_blueprint(bp_auth)
    app.register_blueprint(bp_docs)
    app.register_blueprint(bp_ebooks)
    app.register_blueprint(bp_user)

    # map the blueprint's login() func to Flask-Login
    app.login_manager.login_view = 'auth.login'


def setup_db_session():
    from flask import current_app
    from .extensions.database import get_db
    get_db(current_app)
