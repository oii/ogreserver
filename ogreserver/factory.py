from __future__ import absolute_import
from __future__ import unicode_literals

import salt.client

from flask import Flask
from celery import Celery

from .extensions.celery import queue_configuration, schedule_tasks
from .extensions.config import init_config


def create_app(config=None):
    # instantiate Flask application
    app = Flask(
        __name__,
        static_folder='static/dist',
        static_url_path='/static',
    )

    init_config(app, config=config)

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

    # load the current environment from salt
    caller = salt.client.Caller()
    env = caller.function('grains.item', 'env').get('env', 'dev')
    app.config['env'] = env

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

    # setup JSON encoder extension to integrate with models
    from .extensions.json import init_json
    init_json(app)

    # setup integration with DataDog
    from .extensions.datadog import init_datadog
    init_datadog(app)


def register_blueprints(app):
    # import view blueprints and register with the Flask app
    from .views import bp_core
    from .views.api import bp_api
    from .views.docs import bp_docs
    from .views.download import bp_download
    from .views.ebooks import bp_ebooks
    from .views.user import bp_user
    app.register_blueprint(bp_core)
    app.register_blueprint(bp_api)
    app.register_blueprint(bp_docs)
    app.register_blueprint(bp_download)
    app.register_blueprint(bp_ebooks)
    app.register_blueprint(bp_user)


def register_signals(app):
    from blinker import Namespace
    app.signals = Namespace()

    from .signals import (when_convert_ebook, when_upload_ebook, when_ebook_created,
            when_ebook_updated)

    # register some application signals to help decouple Flask from Celery
    convert_ebook = app.signals.signal('convert-ebook')
    convert_ebook.connect(when_convert_ebook)

    upload_ebook = app.signals.signal('upload-ebook')
    upload_ebook.connect(when_upload_ebook)

    ebook_created = app.signals.signal('ebook-created')
    ebook_created.connect(when_ebook_created)

    ebook_updated = app.signals.signal('ebook-updated')
    ebook_updated.connect(when_ebook_updated)
