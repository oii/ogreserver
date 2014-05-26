from __future__ import absolute_import

import os
import pytest
import random
import shutil
import string

import sqlalchemy

from .. import create_app
from ..database import get_db, create_tables


@pytest.fixture(scope='session')
def app_config():
    return {
        'DEBUG': True,
        'BETA': False,

        'SECRET_KEY': 'its_a_secret',

        'AMQP_BROKER': 'amqp://dev:dev@localhost:5672/dev',
        'CELERY_DEFAULT_QUEUE': 'testing',
        'CELERY_DEFAULT_EXCHANGE_TYPE': 'direct',
        'CELERY_DEFAULT_ROUTING_KEY': 'testing',
        'CELERY_DEFAULT_EXCHANGE': 'testing',

        'AWS_ACCESS_KEY': '',
        'AWS_SECRET_KEY': '',
        'S3_BUCKET': 'oii-ogre-dev',

        'EBOOK_FORMATS': ['mobi','azw','pdf','epub'],
        'DOWNLOAD_LINK_EXPIRY': 10,

        'WHOOSH_BASE': 'test.db',
        'SQLALCHEMY_DATABASE_URI': 'mysql://root:eggs@localhost/test',
        'UPLOADED_EBOOKS_DEST': 'uploads',

        'RETHINKDB_DATABASE': 'test',
    }


@pytest.yield_fixture(scope='session')
def flask_app(app_config):
    app = create_app(app_config)
    yield app
    if os.path.exists(app_config['WHOOSH_BASE']):
        shutil.rmtree(app_config['WHOOSH_BASE'])


@pytest.yield_fixture(scope='session')
def mysqldb(request, flask_app):
    # use raw sqlalchemy for create/drop DB
    engine = sqlalchemy.create_engine('mysql://root:eggs@localhost/mysql')

    def run_query(sql):
        # get the internal connection obj, close the open transaction, then run
        conn = engine.connect()
        conn.execute('commit')
        conn.execute(sql)
        conn.close()

    # create a test database using sqlalchemy
    run_query('drop database if exists test')
    run_query('create database test')

    with flask_app.test_request_context():
        # init app tables into test database
        create_tables(flask_app)
        db_session = get_db(flask_app)
        yield db_session

    # cleanup the test mysql db
    run_query('drop database test')


@pytest.fixture(scope='session')
def user(request, mysqldb):
    from ..models.user import User
    # create random username
    username = ''.join(random.choice(string.ascii_lowercase) for n in range(6))
    # create user in auth DB
    user = User(username, password=username, email='{}@example.com'.format(username))
    mysqldb.add(user)
    mysqldb.commit()
    return user


@pytest.fixture(scope='session')
def datastore(request):
    import rethinkdb as r
    conn = r.connect('localhost', 28015).repl()

    if 'test' in r.db_list().run(conn):
        r.db_drop('test').run(conn)

    # create test datebase
    r.db_create('test').run(conn)
    r.db('test').table_create('ebooks', primary_key='ebook_id').run()
    r.db('test').table_create('versions', primary_key='version_id').run()
    r.db('test').table_create('formats', primary_key='md5_hash').run()
    r.db('test').table('versions').index_create('ebook_id').run()
    r.db('test').table('versions').index_wait('ebook_id').run()
    r.db('test').table('formats').index_create('version_id').run()
    r.db('test').table('formats').index_wait('version_id').run()

    # remove test database
    def fin():
        conn = r.connect('localhost', 28015)
        r.db_drop('test').run(conn)
        conn.close()
    request.addfinalizer(fin)
