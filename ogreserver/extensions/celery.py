from __future__ import absolute_import

import importlib

from celery.schedules import crontab
from kombu import Exchange, Queue


def queue_configuration():
    config = {}

    # Explicit celery exchange/queue setup
    config['CELERY_CREATE_MISSING_QUEUES'] = False

    # Setup two different queues
    config['CELERY_QUEUES'] = (
        Queue('ogreserver', Exchange('ogreserver', type='direct'), routing_key='ogreserver'),
        Queue('conversion', Exchange('conversion', type='direct'), routing_key='convert'),
    )

    # Configure default queue
    config['CELERY_DEFAULT_QUEUE'] = 'ogreserver'
    config['CELERY_DEFAULT_EXCHANGE'] = 'ogreserver'
    config['CELERY_DEFAULT_ROUTING_KEY'] = 'ogreserver'

    return config


def schedule_tasks():
    # setup the celerybeat schedule for periodic tasks
    return {
        'CELERYBEAT_SCHEDULE': {
            'conversion': {
                'task': 'ogreserver.tasks.conversion_search',
                'schedule': crontab(hour=9, minute=1)
            },
        }
    }


def register_tasks(flask_app, pytest=False):
    with flask_app.app_context():
        # configure higher level package for pytest
        if pytest is True:
            package_dir = 'ogre.ogreserver'
        else:
            package_dir = 'ogreserver'

        # import celery tasks with Flask app_context
        importlib.import_module('.tasks', package_dir)
