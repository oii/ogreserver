from __future__ import absolute_import

import logging


def init_logging(app):
    # set logging level for production
    if app.debug is False:
        app.logger.setLevel(app.config.get('LOGGING_LEVEL', logging.ERROR))

    # setup the log format
    app.debug_log_format = '%(asctime)s [%(levelname)s] in %(module)s %(message)s'
    log_date_format = '%d/%m/%Y %H:%M:%S'
    app.logger.handlers[0].formatter.datefmt = log_date_format

    if 'TESTING' in app.config and app.config['TESTING'] is True:
        # during integration tests log to a file, since Flask is running on a background thread
        handler = logging.FileHandler(app.config['TESTING_LOG_PATH'])
        handler.setFormatter(
            logging.Formatter(app.debug_log_format, datefmt=log_date_format)
        )
        app.logger.addHandler(handler)
