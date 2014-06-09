from __future__ import absolute_import

import logging


def init_logging(app):
    # set logging level for production
    if app.debug is False:
        app.logger.setLevel(app.config['LOGGING_LEVEL'])

    if 'TESTING' in app.config and app.config['TESTING'] is True:
        # during integration tests log to a file, since Flask is running on a background thread
        handler = logging.FileHandler(app.config['TESTING_LOG_PATH'])
        handler.setFormatter(
            logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
        )
        app.logger.addHandler(handler)
