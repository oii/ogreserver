#!/usr/bin/env python
from __future__ import absolute_import
from flask.ext.script import Manager
from flask.ext.celery import install_commands as install_celery_commands

from ogreserver import app, tasks

manager = Manager(app)
install_celery_commands(manager)

@manager.command
def hello():
    print "hello"

if __name__ == "__main__":
    manager.run()
