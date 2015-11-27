from __future__ import absolute_import
from __future__ import unicode_literals

import os

from flask import Flask
from celery import Celery

from .extensions.celery import queue_configuration, schedule_tasks

if os.path.exists(os.path.join(os.getcwd(), 'flask.app.conf.py')):
    flask_conf = os.path.join(os.getcwd(), 'flask.app.conf.py')
elif os.path.exists('/etc/ogre/flask.app.conf.py'):
    flask_conf = '/etc/ogre/flask.app.conf.py'


class StaticFolderFlask(Flask):
    '''
    Make Flask's static_folder option configurable via flask.app.conf.py
    '''
    @property
    def static_folder(self):
        '''
        Return configured STATIC_DIR or Flask default of "static"
        '''
        if self.config.get('STATIC_DIR') is not None:
            return os.path.join(self.root_path, self.config.get('STATIC_DIR'))
        else:
            return 'static'

    @static_folder.setter
    def static_folder(self, value):
        pass


def create_app(config=None):
    # instantiate Flask application
    app = StaticFolderFlask(__name__)

    if config is not None and type(config) is dict:
        app.config.update(config)
    else:
        try:
            app.config.from_pyfile(flask_conf)
        except IOError:
            raise Exception('Missing application config! No file at {}'.format(flask_conf))

    def setup_db_before_request():
        # setup DB connection for each request via Flask.before_request()
        from .extensions.database import setup_db_session
        setup_db_session(app)

    # import SQLAlchemy disconnect and map to Flask request shutdown
    from .extensions.database import shutdown_db_session
    app.before_request(setup_db_before_request)
    app.teardown_appcontext(shutdown_db_session)

    # setup application logging
    from .extensions.logging import init_logging
    init_logging(app)

    return app


def make_celery(app):
    # create Celery app object
    celery = Celery(app.import_name, broker=app.config['BROKER_URL'])

    # load config defined in flask.app.py, queue config & celerybeat schedule
    celery.conf.update(app.config)
    celery.conf.update(queue_configuration())
    celery.conf.update(schedule_tasks())

    # http://flask.pocoo.org/docs/0.10/patterns/celery
    TaskBase = celery.Task
    class ContextTask(TaskBase):
        abstract = True
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)
    celery.Task = ContextTask
    return celery


def configure_extensions(app):
    # init Whoosh for full-text search
    from .extensions.whoosh import init_whoosh
    app.whoosh = init_whoosh(app)

    # setup Flask-Security
    from .extensions.flask_security import init_security, add_user_to_globals
    app.security = init_security(app)
    app.before_request(add_user_to_globals)

    # setup Flask-Uploads
    from .extensions.flask_uploads import init_uploads
    app.uploaded_ebooks, app.uploaded_logs = init_uploads(app)

    # setup Flask-Markdown
    from flaskext.markdown import Markdown
    Markdown(app, extensions=['footnotes'])

    # setup Flask-Markdown
    from .extensions.jinja import init_jinja
    init_jinja(app)


def register_blueprints(app):
    # import view blueprints and register with the Flask app
    from .views import bp_core
    from .views.api import bp_api
    from .views.docs import bp_docs
    from .views.ebooks import bp_ebooks
    from .views.user import bp_user
    app.register_blueprint(bp_core)
    app.register_blueprint(bp_api)
    app.register_blueprint(bp_docs)
    app.register_blueprint(bp_ebooks)
    app.register_blueprint(bp_user)


def register_signals(app):
    from blinker import Namespace
    app.signals = Namespace()

    from .signals import when_convert_ebook, when_store_ebook, when_ebook_created, when_ebook_updated

    # register some application signals to help decouple Flask from Celery
    convert_ebook = app.signals.signal('convert-ebook')
    convert_ebook.connect(when_convert_ebook)

    store_ebook = app.signals.signal('store-ebook')
    store_ebook.connect(when_store_ebook)

    ebook_created = app.signals.signal('ebook-created')
    ebook_created.connect(when_ebook_created)

    ebook_updated = app.signals.signal('ebook-updated')
    ebook_updated.connect(when_ebook_updated)
