from __future__ import absolute_import

from .extensions.celery import celery

# setup celery with Flask config
from .runflask import app
celery.config_from_object(app.config)
