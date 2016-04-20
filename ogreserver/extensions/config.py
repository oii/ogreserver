from __future__ import absolute_import
from __future__ import unicode_literals

import os


def init_config(app, config=None):
    # load supplied dict param
    if config is not None and type(config) is dict:
        app.config.update(config)
    else:
        # try current folder, and then /etc/ogre/
        if os.path.exists(os.path.join(os.getcwd(), 'flask.app.conf.py')):
            flask_conf = os.path.join(os.getcwd(), 'flask.app.conf.py')
        elif os.path.exists('/etc/ogre/flask.app.conf.py'):
            flask_conf = '/etc/ogre/flask.app.conf.py'

        try:
            app.config.from_pyfile(flask_conf)
        except IOError:
            raise Exception('Missing application config! No file at {}'.format(flask_conf))
