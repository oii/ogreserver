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

    # import SQLAlchemy disconnect and map to Flask request shutdown
    from .database import shutdown_db_session
    app.before_request(setup_db_session)
    app.teardown_appcontext(shutdown_db_session)

    # import Celery
    from .celery import init_app as init_celery
    app.celery = init_celery(app)

    # init Whoosh for full-text search
    from .whoosh import init_app as init_whoosh
    app.whoosh = init_whoosh(app)

    # setup Flask-Login
    from .flask_login import init_app as init_login
    app.login_manager = init_login(app)

    # setup Flask-Uploads
    from .flask_uploads import init_app as init_uploads
    app.uploads = init_uploads(app)

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
