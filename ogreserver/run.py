import os

from . import create_app

app = create_app(
    os.path.join(os.getcwd(), 'ogreserver/config/flask.app.conf.py')
)
