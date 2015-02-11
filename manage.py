#! /usr/bin/env python

from __future__ import absolute_import

import datetime
import json
import os
import sys

import boto

from flask.ext.script import Manager
from sqlalchemy.exc import IntegrityError, ProgrammingError

import rethinkdb as r
from rethinkdb.errors import RqlRuntimeError

from ogreserver.factory import create_app, make_celery
from ogreserver.extensions.celery import register_tasks
from ogreserver.extensions.database import setup_db_session, create_tables, setup_roles
from ogreserver.utils import connect_s3

app = create_app()
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
    r.table('sync_events').delete().run()
    if os.path.exists('search.db'):
        import shutil, subprocess
        shutil.rmtree('search.db')
        subprocess.call('kill -HUP $(cat /tmp/gunicorn-ogreserver.pid)', shell=True)
    conn.close()


@manager.command
def lb(ebook_id):
    from ogreserver.models.datastore import DataStore
    ds = DataStore(app.config, logger=None)
    ebook = ds.load_ebook(ebook_id)

    # if no ebook_id supplied, check if supplied param is file_hash
    if ebook is None:
        ebook = ds.load_ebook_by_file_hash(ebook_id, match=True)
        if ebook is None:
            print 'Not found'
            return

    for v in ebook['versions']:
        v['date_added'] = v['date_added'].isoformat()
        del(v['ebook_id'])
        for f in v['formats']:
            del(f['version_id'])

    # pretty print json with colorized ebook_id/file_hash
    print json.dumps(ebook, indent=2).replace(
        ebook_id, '\033[92m{}\033[0m'.format(ebook_id)
    )


@manager.command
def create_user(username, password, email, role='user', confirmed=False, test=False):
    """
    Create a new user for OGRE

    test (bool)
        Only check if user has been created; don't actually do anything
    """
    try:
        # load a user
        setup_db_session(app)
        from ogreserver.models.user import User
        user = User.query.filter_by(username=username).first()

    except ProgrammingError as e:
        if "doesn't exist" in str(e):
            print 'You must run init_ogre command first!'
            sys.exit(1)
        else:
            raise e

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
            try:
                # celery is required for flask_security as it imports tasks.py
                app.celery = make_celery(app)
                register_tasks(app)

                from ogreserver.extensions.flask_security import init_security

                app.security = init_security(app)
                user = app.security.datastore.create_user(
                    username=username, email=email, password=password
                )
                if confirmed:
                    from flask.ext.security.confirmable import confirm_user
                    confirm_user(user)

                app.security.datastore.commit()

                print "Created user {} with role '{}'".format(username, role)

            except IntegrityError:
                print 'A user with this email address already exists'
                sys.exit(1)
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
    s3 = connect_s3(app.config)

    # check bucket already exists
    aws_setup = False
    for b in s3.get_all_buckets():
        if b.name == app.config['S3_BUCKET']:
            aws_setup = True

    # check mysql DB created
    try:
        setup_db_session(app)
        from ogreserver.models.user import User
        User.query.first()
        db_setup = True
    except ProgrammingError:
        db_setup = False

    # check rethinkdb initialized
    conn = r.connect('localhost', 28015)
    try:
        r.db('ogreserver').table('ebooks').run(conn)
        rdb_setup = True
    except RqlRuntimeError:
        rdb_setup = False

    if test is True:
        # only report state in test mode
        if aws_setup is True and db_setup is True and rdb_setup is True:
            print 'Already setup'
            sys.exit(0)
        else:
            print 'Not setup'
            sys.exit(1)
    else:
        if aws_setup is True and db_setup is True and rdb_setup is True:
            print 'You have already initialized OGRE :D'
            sys.exit(1)

        # create the local mysql database from our models
        if db_setup is False:
            create_tables(app)
            # celery is required for setup_roles as it imports tasks.py via flask_security
            app.celery = make_celery(app)
            register_tasks(app)
            setup_roles(app)

        if aws_setup is False:
            try:
                if not app.config['DEBUG']:
                    s3.create_bucket(app.config['S3_BUCKET'], location=app.config['AWS_REGION'])
                    print 'Created S3 bucket in {}'.format(app.config['AWS_REGION'])
                else:
                    s3.create_bucket(app.config['S3_BUCKET'])
                    print 'Created S3 bucket'

            except boto.exception.S3ResponseError as e:
                sys.stderr.write('Failed verifying or creating S3 bucket.. ({})\n'.format(e.error_message))
                sys.exit(1)
            except boto.exception.S3CreateError as e:
                if e.error_code == 'BucketAlreadyExists':
                    sys.stderr.write('Bucket name already in use! ({})\n'.format(e.error_message))
                    sys.exit(1)
                else:
                    raise e

        if rdb_setup is False:
            # create a database and a couple of tables
            r.db_create('ogreserver').run(conn)
            r.db('ogreserver').table_create('ebooks', primary_key='ebook_id').run(conn)
            r.db('ogreserver').table_create('versions', primary_key='version_id').run(conn)
            r.db('ogreserver').table_create('formats', primary_key='file_hash').run(conn)
            r.db('ogreserver').table_create('authors', primary_key='author_id').run(conn)
            r.db('ogreserver').table_create('sync_events').run(conn)
            set_indexes()

    print 'Succesfully initialized OGRE'


@manager.command
def set_indexes():
    def create_index(table, name, index=None):
        conn = r.connect("localhost", 28015, db='ogreserver')
        if name not in r.table(table).index_list().run(conn):
            start = datetime.datetime.now()
            if index is None:
                r.table(table).index_create(name).run(conn)
            else:
                r.table(table).index_create(name, index).run(conn)
            r.table(table).index_wait(name).run(conn)
            print "index '{}' created in {}".format(name, datetime.datetime.now()-start)

    # create the rethinkdb indexes used by ogreserver
    create_index(
        'ebooks', 'authortitle',
        index=[r.row['author'].downcase(), r.row['title'].downcase()]
    )
    create_index('ebooks', 'asin', index=r.row['meta']['asin'])
    create_index('ebooks', 'isbn', index=r.row['meta']['isbn'])
    create_index('versions', 'ebook_id')
    create_index('versions', 'original_filehash')
    create_index('versions', 'ebook_username', index=[r.row['ebook_id'], r.row['username']])
    create_index('formats', 'version_id')
    create_index('formats', 'uploaded')
    create_index('formats', 'uploaded_by')
    create_index('formats', 'uploadedby_dedrm', index=[r.row['uploaded_by'], r.row['dedrm']])
    create_index('sync_events', 'username')
    create_index('sync_events', 'timestamp')
    create_index('sync_events', 'user_new_books_count', index=[r.row['username'], r.row['new_books_count']])


@manager.command
def show_s3(test=False):
    if test:
        # import the configuration for pytest runs
        from conftest import app_config
        config = app_config()
    else:
        config = app.config

    # connect to S3
    s3 = connect_s3(config)
    bucket = s3.get_bucket(config['S3_BUCKET'])
    for item in bucket.list():
        print item


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
