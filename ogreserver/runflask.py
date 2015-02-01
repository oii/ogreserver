from __future__ import absolute_import

from .factory import create_app, make_celery, configure_extensions, \
        register_blueprints, register_signals
from .extensions.celery import register_tasks

app = create_app()
app.celery = make_celery(app)
register_tasks(app)
register_signals(app)
configure_extensions(app)
register_blueprints(app)
