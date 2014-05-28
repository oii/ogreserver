from __future__ import absolute_import

from celery import Celery


def init_app(app):
    celery = Celery(broker=app.config['AMQP_BROKER'])
    celery.config_from_object(app.config)
