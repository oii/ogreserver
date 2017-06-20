O.G.R.E.
========

[![Build Status](http://img.shields.io/travis/oii/ogre.svg?style=flat-square&branch=develop)][travis]
[![CircleCI](https://img.shields.io/circleci/project/github/oii/ogre.svg)][circleci]
[![Code Health](https://landscape.io/github/oii/ogre/dev/landscape.svg?style=flat)](https://landscape.io/github/oii/ogre/dev)
[![Made By Oii](http://img.shields.io/badge/made%20by-oii-blue.svg?style=flat-square)][author]
[![BSD License](http://img.shields.io/badge/license-BSD-red.svg?style=flat-square)][license]

[travis]: http://travis-ci.org/oii/ogre
[circleci]: https://circleci.com/gh/oii/ogre
[author]: http://github.com/oii/ogre
[license]: http://github.com/oii/ogre/blob/master/LICENSE


OGRE is an ebook storage and synchronisation service.

OGRE comes in two parts:
  - a server built in Python relying on Flask and Celery
  - a cross-platform client script in Python which synchronises ebooks to the server.


Ogreserver
----------

A `Vagrantfile` is included to start a development OGRE server.

    cd ogreserver/config
    vagrant up

SSH into the VM and bootstrap the server with the salt CM configs:

    vagrant ssh
    sudo salt-call state.apply

Once this is complete, you should have a working OGRE server. You can check things are running with:

    sudo supervisorctl status
    ogreserver:celerybeat            RUNNING   pid 17857, uptime 0:04:22
    ogreserver:celeryd.high          RUNNING   pid 17859, uptime 0:04:22
    ogreserver:celeryd.low           RUNNING   pid 17858, uptime 0:04:22
    ogreserver:gunicorn              RUNNING   pid 17860, uptime 0:04:22
    s3proxy                          RUNNING   pid 17856, uptime 0:04:22

A preconfigured tmux dev environment is available also:

    tmux attach


Ogreclient
----------

The client app to sync with the server can be run with the `ogre` command. Install it locally into
a virtualenv:

    cd ogreclient
    pip install -e .

And run a sync to your VM:

    ogre --ogreserver 172.16.8.128:8005
