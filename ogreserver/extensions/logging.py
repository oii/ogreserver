from __future__ import absolute_import

import logging

try:
    from raven import Client
    from raven.contrib.celery import register_signal, register_logger_signal
    from raven.contrib.flask import Sentry
    from raven.handlers.logging import SentryHandler
except ImportError:
    pass

import salt.client


def init_logging(app):
    if app.config['DEBUG'] is True:
        app.logger.setLevel(logging.DEBUG)
    else:
        # set logging level for production
        app.logger.setLevel(app.config.get('LOGGING_LEVEL', logging.ERROR))

    # setup the log format on Flask's logger
    app.logger.handlers[0].setFormatter(
        logging.Formatter(
            '%(asctime)s [%(levelname)s] in %(module)s %(message)s', '%d/%m/%Y %H:%M:%S'
        )
    )

    # extra logging during test runs
    if 'TESTING' in app.config and app.config['TESTING'] is True:
        extra_testing_setup(app)

    # production/staging error logging on Sentry
    if app.config.get('ENV', 'dev') != 'dev':
        init_sentry(app)


def init_sentry(app):
    # retrieve current git commitish for HEAD
    caller = salt.client.Caller()
    data = caller.function('grains.item', 'git_revision')

    # sentry config
    sentry_client = Client(
        dsn=app.config['SENTRY_DSN'],
        environment=app.config['ENV'],
        release=data['git_revision']
    )
    sentry = Sentry(client=sentry_client)
    sentry.init_app(app)

    # hook into Celery
    register_logger_signal(sentry_client)
    register_signal(sentry_client)

    # add Sentry handler to Flask logger
    handler = SentryHandler(app.config['SENTRY_DSN'])
    app.logger.addHandler(handler)


def extra_testing_setup(app):
    '''
    During integration tests log to a file, since Flask is running on a
    background thread
    '''
    handler = logging.FileHandler(app.config['TESTING_LOG_PATH'])
    handler.setFormatter(
        logging.Formatter(
            '%(asctime)s [%(levelname)s] in %(module)s %(message)s', '%d/%m/%Y %H:%M:%S'
        )
    )
    app.logger.addHandler(handler)
