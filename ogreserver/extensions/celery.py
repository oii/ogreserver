from __future__ import absolute_import

import datetime
import importlib

from kombu import Exchange, Queue


def queue_configuration():
    config = {}

    # explicit celery exchange/queue setup
    config['CELERY_CREATE_MISSING_QUEUES'] = False

    # setup two different queues
    exchange = Exchange('ogreserver', type='direct')
    config['CELERY_QUEUES'] = (
        Queue('low', exchange, routing_key='low'),
        Queue('normal', exchange, routing_key='normal'),
        Queue('high', exchange, routing_key='high'),
    )

    # configure default queue
    config['CELERY_DEFAULT_QUEUE'] = 'normal'
    config['CELERY_DEFAULT_EXCHANGE'] = 'ogreserver'
    config['CELERY_DEFAULT_ROUTING_KEY'] = 'normal'

    return config


def schedule_tasks():
    # setup the celerybeat schedule for periodic tasks
    return {
        'CELERYBEAT_SCHEDULE': {
            'conversion': {
                'task': 'ogreserver.tasks.conversion_search',
                'schedule': datetime.timedelta(minutes=30)
            },
        }
    }


def register_tasks(flask_app):
    with flask_app.app_context():
        # import celery tasks with Flask app_context
        importlib.import_module('.tasks', 'ogreserver')
