O.G.R.E.
========

OGRE runs on a Debian server and as such is built for Python 2.6.


Ogreserver Prerequisites
------------------------

* aptitude install virtualenvwrapper python-pip python-dev
* aptitude install rabbitmq-server
* aptitude install mysql-server libmysqlclient-dev


Ogreserver Install Instructions
-------------------------------

1. Clone this repo to your server
2. Init a virtualenv for OGRE:

    $ mkvirtualenv ogre
    $ pip install -r config/requirements.txt

3. Create the auth DB:

    $ mysql -u root -p < config/schema-mysql2.sql

