#! /usr/bin/env python

from __future__ import absolute_import

import datetime
import os
import sys

from flask.ext.script import Manager
from sqlalchemy.exc import IntegrityError, ProgrammingError

import rethinkdb as r
from rethinkdb.errors import RqlRuntimeError

from ogreserver import create_app
from ogreserver.extensions.database import get_db, create_tables

app = create_app(
    os.path.join(os.getcwd(), 'ogreserver/config/flask.app.conf.py')
)
manager = Manager(app)


@manager.command
def cleardb():
    if app.debug is False:
        print 'You cannot run cleardb when not in DEBUG!!'
        return
    conn = r.connect("localhost", 28015, db='ogreserver').repl()
    r.table('ebooks').delete().run()
    r.table('versions').delete().run()
    r.table('formats').delete().run()
    if os.path.exists('search.db'):
        import shutil, subprocess
        shutil.rmtree('search.db')
        subprocess.call('kill -HUP $(cat /tmp/gunicorn-ogreserver.pid)', shell=True)
    conn.close()


@manager.command
def verify_s3():
    import logging
    logging.basicConfig(filename="boto.log", level=logging.DEBUG)
    from ogreserver.models.datastore import DataStore
    print DataStore.get_missing_books(username="mafro", verify_s3=True)


@manager.command
def create_user(username, password, email, test=False):
    """
    Create a new user for OGRE

    test (bool)
        Only check if user has been created; don't actually do anything
    """
    # load a user
    get_db(app)
    from ogreserver.models.user import User
    user = User.query.filter_by(username=username).first()

    if test is True:
        # only report state in test mode
        if user is None:
            print "User doesn't exist"
            sys.exit(1)
        else:
            print 'User {} exists'.format(username)
            sys.exit(0)
    else:
        if user is None:
            user = User(username, password, email)
            db_session = get_db(app)
            db_session.add(user)
            try:
                db_session.commit()
            except IntegrityError:
                print 'A user with this email address already exists'
                sys.exit(1)

            print 'Created user {}'.format(username)
        else:
            print 'User {} already exists'.format(username)
            sys.exit(1)


@manager.command
def rebuild_index():
    "Reindex the entire DB into Whoosh."
    # TODO implement
    pass


@manager.command
def init_ogre(test=False):
    """
    Initialize the AWS S3 bucket & RethinkDB storage for OGRE.

    test (bool)
        Only check if OGRE has been setup; don't actually do anything
    """

    # init S3
    import boto
    s3 = boto.connect_s3(
        app.config['AWS_ACCESS_KEY'],
        app.config['AWS_SECRET_KEY']
    )

    # check bucket already exists
    aws_setup = False
    for b in s3.get_all_buckets():
        if b.name == app.config['S3_BUCKET']:
            aws_setup = True

    # check mysql DB created
    try:
        get_db(app)
        from ogreserver.models.user import User
        User.query.first()
        db_setup = True
    except ProgrammingError:
        db_setup = False

    # check rethinkdb initialized
    conn = r.connect("localhost", 28015)
    try:
        r.db("ogreserver").table("ebooks").run(conn)
        rdb_setup = True
    except RqlRuntimeError:
        rdb_setup = False

    if test is True:
        # only report state in test mode
        if aws_setup is True and db_setup is True and rdb_setup is True:
            print "Already setup"
            sys.exit(0)
        else:
            print "Not setup"
            sys.exit(1)
    else:
        if aws_setup is True and db_setup is True and rdb_setup is True:
            sys.stderr.write("You have already initialized OGRE!\n")
            sys.exit(1)

        # create the local mysql database from our models
        if db_setup is False:
            create_tables(app)

        if aws_setup is False:
            try:
                s3.create_bucket(app.config['S3_BUCKET'], location=boto.s3.connection.Location.EU)
            except boto.exception.S3CreateError as e:
                if e.error_code == "BucketAlreadyExists":
                    sys.stderr.write("Bucket name already in use!\n  {0}\n".format(e.error_message))
                else:
                    sys.stderr.write("{0}\n".format(e.error_message))
                sys.exit(1)

        if rdb_setup is False:
            # create a database and a couple of tables
            r.db_create('ogreserver').run(conn)
            r.db('ogreserver').table_create('ebooks', primary_key='ebook_id').run(conn)
            r.db('ogreserver').table_create('versions', primary_key='version_id').run(conn)
            r.db('ogreserver').table_create('formats', primary_key='file_hash').run(conn)
            set_indexes()

    print "Succesfully initialized OGRE"


@manager.command
def set_indexes():
    def create_index(table, name):
        conn = r.connect("localhost", 28015, db='ogreserver')
        if name not in r.table(table).index_list().run(conn):
            start = datetime.datetime.now()
            r.table(table).index_create(name).run(conn)
            r.table(table).index_wait(name).run(conn)
            print "index '{}' created in {}".format(name, datetime.datetime.now()-start)

    # create the rethinkdb indexes used by ogreserver
    create_index('versions', 'ebook_id')
    create_index('formats', 'version_id')


@manager.command
def check_pip():
    import xmlrpclib
    import pip

    pypi = xmlrpclib.ServerProxy('http://pypi.python.org/pypi')
    for dist in pip.get_installed_distributions():
        available = pypi.package_releases(dist.project_name)
        if not available:
            # Try to capitalize pkg name
            available = pypi.package_releases(dist.project_name.capitalize())

        if not available:
            msg = 'no releases at pypi'
        elif available[0] != dist.version:
            msg = '{} available'.format(available[0])
        else:
            msg = 'up to date'
        pkg_info = '{dist.project_name} {dist.version}'.format(dist=dist)
        print '{pkg_info:40} {msg}'.format(pkg_info=pkg_info, msg=msg)

if __name__ == "__main__":
    manager.run()
