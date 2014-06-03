from __future__ import absolute_import

# create Celery
from celery import Celery
celery = Celery()


def init_celery(app):
    # setup celery with Flask config
    celery.config_from_object(app.config)
    return celery
