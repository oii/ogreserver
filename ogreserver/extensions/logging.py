from __future__ import absolute_import

import logging


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
