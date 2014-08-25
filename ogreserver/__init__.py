from __future__ import absolute_import

# import Flask library
from flask import Flask


def create_app(config):
    # instantiate Flask application
    app = Flask(__name__)

    if isinstance(config, basestring):
        try:
            app.config.from_pyfile(config)
        except IOError:
            raise Exception('Missing application config! No file at {}'.format(config))

    elif type(config) is dict:
        app.config.update(config)

    # create Celery
    from .extensions.celery import init_celery
    app.celery = init_celery(app)

    # import SQLAlchemy disconnect and map to Flask request shutdown
    from .extensions.database import shutdown_db_session
    app.before_request(setup_db_session)
    app.teardown_appcontext(shutdown_db_session)

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

    # setup application logging
    from .extensions.logging import init_logging
    init_logging(app)

    # setup Flask-Markdown
    from flaskext.markdown import Markdown
    Markdown(app, extensions=['footnotes'])

    # import views as a blueprint and register with Flask the app
    from .views import views
    app.register_blueprint(views)

    # map the blueprint's login() func to Flask-Login
    app.login_manager.login_view = 'views.login'

    return app


def setup_db_session():
    from flask import current_app
    from .extensions.database import get_db
    get_db(current_app)
