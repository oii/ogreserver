from __future__ import absolute_import

from .factory import create_app, make_celery, configure_extensions, register_blueprints
from .extensions.celery import register_tasks

app = create_app()
app.celery = make_celery(app)
register_tasks(app)
configure_extensions(app)
register_blueprints(app)
