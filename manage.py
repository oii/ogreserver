#! /usr/bin/env python

from __future__ import absolute_import

import json
import os
import subprocess
import sys
import time

import boto
import salt.client

from flask.ext.script import Manager
from sqlalchemy.exc import IntegrityError, ProgrammingError

from ogreserver.factory import create_app, make_celery, register_signals
from ogreserver.extensions.celery import register_tasks
from ogreserver.extensions.database import setup_db_session, create_tables, setup_roles
from ogreserver.models.ebook import Ebook, Version, Format, SyncEvent
from ogreserver.models.user import User
from ogreserver.stores import ebooks as ebook_store
from ogreserver.utils.generic import make_temp_directory
from ogreserver.utils.s3 import connect_s3

app = create_app()
manager = Manager(app)

@manager.command
def convert():
    from ogreserver.models.conversion import Conversion
    app.celery = make_celery(app)
    register_tasks(app)
    register_signals(app)
    conversion = Conversion(app.config)
    conversion.search()


@manager.command
def cleardb():
    db_session = setup_db_session(app)

    caller = salt.client.Caller()
    env = caller.function('grains.item', 'env').get('env', 'dev')
    if env != 'dev':
        print 'You cannot run cleardb when not in DEBUG!!'
        return
    Format.query.delete()
    Version.query.delete()
    Ebook.query.delete()
    SyncEvent.query.delete()
    db_session.commit()
    if os.path.exists('/var/ogre/search.db'):
        import shutil, subprocess
        shutil.rmtree('/var/ogre/search.db')
        subprocess.call('pkill -HUP gunicorn', shell=True)


@manager.command
def lb(ebook_id):
    setup_db_session(app)

    ebook = ebook_store.load_ebook(ebook_id)

    # if no ebook_id supplied, check if supplied param is file_hash
    if ebook is None:
        ebook = ebook_store.load_ebook_by_file_hash(ebook_id)
        if ebook is None:
            print 'Not found'
            return

    # pretty print json with colorized ebook_id/file_hash
    print json.dumps(ebook, indent=2).replace(
        ebook.id, '\033[92m{}\033[0m'.format(ebook.id)
    )


@manager.command
def rebuild_metadata(foreground=False):
    """
    Reload all metadata from external APIs. Use with caution!
    """
    # setup celery for rebuilding meta in background
    app.celery = make_celery(app)
    register_tasks(app)
    register_signals(app)

    from ogreserver.tasks import query_ebook_metadata

    # run metadata task for all ebooks
    for ebook in Ebook.query.all():
        if foreground:
            query_ebook_metadata(ebook.id)
        else:
            query_ebook_metadata.delay(ebook.id)


@manager.command
def rebuild_index(foreground=False):
    """
    Reindex the entire DB into Whoosh
    """
    # setup celery for rebuilding meta in background
    app.celery = make_celery(app)
    register_tasks(app)
    register_signals(app)

    from ogreserver.tasks import index_for_search

    # run search index task for all ebooks
    for ebook in Ebook.query.all():
        if foreground:
            index_for_search(ebook.id)
        else:
            index_for_search.delay(ebook.id)


@manager.command
def create_user(username, password, email, role='user', confirmed=False, test=False):
    """
    Create a new user for OGRE

    test (bool)
        Only check if user has been created; don't actually do anything
    """
    setup_db_session(app)

    try:
        # load a user
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
def init_ogre(test=False):
    """
    Initialize the DB and AWS S3 bucket for OGRE.

    test (bool)
        Only check if OGRE has been setup; don't actually do anything
    """
    setup_db_session(app)

    try:
        # check mysql DB created
        User.query.first()
        db_setup = True
    except ProgrammingError:
        db_setup = False

    if test is True:
        # only report state in test mode
        if db_setup is True:
            print 'Already setup'
            sys.exit(0)
        else:
            print 'Not setup'
            sys.exit(1)
    else:
        if db_setup is True:
            print 'You have already initialized OGRE :D'
            sys.exit(1)

        # create the local mysql database from our models
        if db_setup is False:
            create_tables(app)
            # celery is required for setup_roles as it imports tasks.py via flask_security
            app.celery = make_celery(app)
            register_tasks(app)
            setup_roles(app)

    caller = salt.client.Caller()
    env = caller.function('grains.item', 'env').get('env', 'dev')
    if env == 'dev':
        create_ogre_s3_dev()

    print 'Succesfully initialized OGRE'



@manager.command
def create_ogre_s3_dev():
    # create S3 buckets in dev (handled by terraform in prod)
    s3 = connect_s3(app.config)

    for bucket_name in ('EBOOK', 'STATIC', 'DIST', 'BACKUP'):
        try:
            s3.create_bucket(
                app.config['{}_S3_BUCKET'.format(bucket_name)].format('dev')
            )

        except boto.exception.S3ResponseError as e:
            sys.stderr.write('Failed verifying or creating S3 bucket.. ({})\n'.format(e.error_message))
            sys.exit(1)
        except boto.exception.S3CreateError as e:
            if e.error_code == 'BucketAlreadyExists':
                sys.stderr.write('Bucket name already in use! ({})\n'.format(e.error_message))
                sys.exit(1)
            elif e.error_code == 'BucketAlreadyOwnedByYou':
                pass
            else:
                raise e


@manager.command
def show_s3(test=False):
    if test:
        # import the configuration for pytest runs
        from conftest import app_config
        config = app_config()
    else:
        config = app.config

    caller = salt.client.Caller()
    env = caller.function('grains.item', 'env').get('env', 'dev')

    # connect to S3
    s3 = connect_s3(config)
    bucket = s3.get_bucket(config['EBOOK_S3_BUCKET'].format(env))
    for item in bucket.list():
        print item


@manager.command
def check_pip():
    import xmlrpclib
    import pip

    pypi = xmlrpclib.ServerProxy('http://pypi.python.org/pypi')
    for dist in sorted(pip.get_installed_distributions(), key=lambda k: k.project_name.lower()):
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


@manager.command
def dump_postgres(identifier):
    """
    Dump postgres to S3
    """
    command = 'postgresdump -h {} -u {} -p{} {} | gzip -qv > {{}}'.format(
        app.config['POSTGRES_HOST'],
        app.config['POSTGRES_USER'],
        app.config['POSTGRES_PASS'],
        app.config['POSTGRES_DB'],
    )
    dump_database_to_s3('postgres', identifier, command)


def dump_database_to_s3(db_type, identifier, command):
    """
    Dump a database to S3

    :param  db_type     "postgres" only
    :param  identifier  unique DB backup id
    :param  command     backup shell command with "{}" placeholder for filename
    """
    caller = salt.client.Caller()
    env = caller.function('grains.item', 'env').get('env', 'dev')

    with make_temp_directory() as tmpdir:
        try:
            filename = '{}_dump_{}_{}.tar.gz'.format(db_type, int(time.time()), identifier)

            subprocess.check_call(
                command.format(os.path.join(tmpdir, filename)),
                shell=True
            )

            # push to S3
            s3 = connect_s3(app.config)
            k = s3.get_bucket(app.config['BACKUP_S3_BUCKET'].format(env)).new_key(filename)
            k.set_contents_from_filename(os.path.join(tmpdir, filename))

            # update latest backup redirect
            k = s3.get_bucket(app.config['BACKUP_S3_BUCKET'].format(env)).new_key(
                '{}_dump_latest.tar.gz'.format(db_type)
            )
            k.set_redirect('/{}'.format(filename))

        except subprocess.CalledProcessError as e:
            sys.stderr.write('Failed dumping {} ({})\n'.format(db_type, e))
            sys.exit(1)


@manager.command
def restore_postgres():
    """
    Restore postgres from S3
    """
    command = 'gunzip --stdout {{}} | postgres -h {} -u {} -p{} {}'.format(
        app.config['POSTGRES_HOST'],
        app.config['POSTGRES_USER'],
        app.config['POSTGRES_PASS'],
        app.config['POSTGRES_DB']
    )
    restore_database_from_s3('postgres', command)


def restore_database_from_s3(db_type, command):
    """
    Restore a database from S3 backup

    :param  db_type     "postgres" only
    :param  command     backup shell command with "{}" placeholder for filename
    """
    caller = salt.client.Caller()
    env = caller.function('grains.item', 'env').get('env', 'dev')

    s3 = connect_s3(app.config)

    # retrieve the filename of the latest backup
    k = s3.get_bucket(app.config['BACKUP_S3_BUCKET'].format(env)).get_key(
        '{}_dump_latest.tar.gz'.format(db_type)
    )
    backup_name = k.get_redirect()[1:]

    with make_temp_directory() as tmpdir:
        k = s3.get_bucket(app.config['BACKUP_S3_BUCKET'].format(env)).get_key(backup_name)

        try:
            with open(os.path.join(tmpdir, backup_name), 'wb') as f:
                k.get_contents_to_file(f)

            subprocess.check_call(
                command.format(os.path.join(tmpdir, backup_name)),
                shell=True
            )
        except subprocess.CalledProcessError as e:
            sys.stderr.write('Failed restoring {} ({})\n'.format(db_type, e))
            sys.exit(1)


@manager.command
def shutdown():
    """
    Prep the application for shutdown:
     - dump postgres to S3
     - set OGRE DNS to point to static page
    """
    # retrieve current git commitish for HEAD
    caller = salt.client.Caller()
    data = caller.function('grains.item', 'git_revision')

    # backup DBs to S3
    dump_postgres(data['git_revision'])


@manager.command
def startup():
    """
    Import DBs at application start
    """
    # restore DBs from S3
    restore_postgres()


if __name__ == "__main__":
    manager.run()
