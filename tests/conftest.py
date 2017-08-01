from __future__ import absolute_import
from __future__ import unicode_literals

import collections
import contextlib
import copy
import datetime
import json
import logging
import os
import random
import shutil
import string
import threading
import yaml

import boto.exception
import mock
import pytest
from sqlalchemy import create_engine
import whoosh

from ogreserver.extensions.database import setup_db_session, create_tables
from ogreserver.utils.s3 import connect_s3
from ogreserver.models.ebook import Ebook, Version, Format
from ogreserver.models.user import User
from ogreserver.search import Search
from ogreserver.stores import ebooks as ebook_store

import fixtures


def pytest_addoption(parser):
    parser.addoption('--only-client',
        action='store_true',
        help='Skip all the server fixtures whose libs are missing for ogreclient'
    )


@pytest.fixture(scope='session')
def app_config():
    FormatConfig = collections.namedtuple('FormatConfig', ('is_valid_format', 'is_non_fiction'))
    return {
        'DEBUG': True,
        'BETA': False,
        'TESTING': True,
        'TESTING_LOG_PATH': 'ogreserver.log',

        'SECRET_KEY': 'its_a_secret',

        'AWS_ADVERTISING_API_ACCESS_KEY': 'its_a_secret',
        'AWS_ADVERTISING_API_SECRET_KEY': 'its_a_secret',
        'AWS_ADVERTISING_API_ASSOCIATE_TAG': 'its_a_secret',

        'GOODREADS_API_KEY': 'its_a_secret',

        'BROKER_URL': 'amqp://dev:dev@localhost:5672/dev',
        'CELERY_DEFAULT_QUEUE': 'testing',
        'CELERY_DEFAULT_EXCHANGE_TYPE': 'direct',
        'CELERY_DEFAULT_ROUTING_KEY': 'testing',
        'CELERY_DEFAULT_EXCHANGE': 'testing',

        'STATIC_BASE_URL': '',
        'STATIC_S3_BUCKET': '',

        'AWS_ACCESS_KEY': '',
        'AWS_SECRET_KEY': '',
        'AWS_REGION': '',
        'EBOOK_S3_BUCKET': 'ogre-testing',
        'DIST_S3_BUCKET': 'ogre-testing',
        'DEDRM_VERSION': '0.0.1',

        'EBOOK_CONTENT_TYPES': {
            'azw3': 'application/vnd.amazon.ebook',
            'epub': 'application/epub+zip',
        },

        'EBOOK_DEFINITIONS': collections.OrderedDict([
            ('mobi', FormatConfig(True, False)),
            ('pdf', FormatConfig(False, True)),
            ('azw3', FormatConfig(True, False)),
            ('epub', FormatConfig(True, False)),
        ]),

        'EBOOK_FORMATS': ['egg', 'mobi', 'azw3'],
        'DOWNLOAD_LINK_EXPIRY': 10,
        'NUM_EBOOKS_FOR_CONVERT': 1,

        'DB_HOST': 'localhost',
        'DB_USER': 'ogre',
        'DB_PASS': 'oii',
        'DB_NAME': 'test',

        'WHOOSH_BASE': 'test.db',
        'UPLOADED_EBOOKS_DEST': 'uploads',
        'UPLOADED_LOGS_DEST': 'logs',

        # store passwords in plaintext during test runs
        'SECURITY_PASSWORD_HASH': 'plaintext',
        'SECURITY_PASSWORD_SALT': 'test',
        'SECURITY_TOKEN_AUTHENTICATION_HEADER': 'Ogre-Key',
        'SECURITY_USER_IDENTITY_ATTRIBUTES': ['email', 'username'],

        # override the flask-security HASHING_SCHEME for fast password hashes
        'SECURITY_HASHING_SCHEMES': ['plaintext'],
        'SECURITY_DEPRECATED_HASHING_SCHEMES': [],
    }


@pytest.yield_fixture(scope='session')
def _flask_app(request, app_config):
    if request.config.getoption('--only-client'):
        yield None
        return

    from ogreserver.factory import create_app, make_celery, configure_extensions, \
            register_blueprints, register_signals
    from ogreserver.extensions.celery import register_tasks

    # mock out salt.client during tests
    with mock.patch('ogreserver.factory.salt'):
        app = create_app(app_config)
    app.testing = True
    app.celery = make_celery(app)
    register_tasks(app)
    configure_extensions(app)
    register_blueprints(app)
    register_signals(app)
    yield app
    if os.path.exists(app_config['WHOOSH_BASE']):
        shutil.rmtree(app_config['WHOOSH_BASE'])


@pytest.yield_fixture(scope='function')
def flask_app(request, _flask_app):
    # mock all signals attached to the Flask app
    for name in _flask_app.signals.keys():
        _flask_app.signals[name] = mock.Mock()
    yield _flask_app


@pytest.fixture(scope='session')
def ogreserver(request, _flask_app):
    if request.config.getoption('--only-client'):
        return

    from wsgiref.simple_server import make_server

    server = make_server('', 6543, _flask_app)
    app_thread = threading.Thread(target=server.serve_forever)
    app_thread.start()
    def fin():
        threading.Thread(target=server.shutdown).start()
    request.addfinalizer(fin)
    return app_thread


def terminate_db_connections(engine, db_name):
    # terminate any existing DB connections
    text = '''
    SELECT pg_terminate_backend(pg_stat_activity.pid)
    FROM pg_stat_activity
    WHERE pg_stat_activity.datname = '{}'
      AND pid <> pg_backend_pid();
    '''.format(db_name)
    engine.execute(text)


@pytest.yield_fixture(scope='session')
def _postgresql(request, _flask_app):
    if request.config.getoption('--only-client'):
        yield None
        return

    # update DB connection string
    _flask_app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}/test'.format(**_flask_app.config)

    # use raw sqlalchemy for create/drop DB
    engine = create_engine(
        'postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}/'.format(**_flask_app.config)
    )

    def run_query(sql):
        # get the internal connection obj, close the open transaction, then run
        conn = engine.connect()
        conn.execute('commit')
        conn.execute(sql)
        conn.close()

    # terminate any existing DB connections
    terminate_db_connections(engine, 'test')

    # create a test database using sqlalchemy
    run_query('drop database if exists test')
    run_query('create database test')

    with _flask_app.test_request_context():
        # init app tables into test database
        db_session = setup_db_session(_flask_app, expire_on_commit=False)
        create_tables(_flask_app)

        # create the ogrebot user
        ogrebot = User(
            'ogrebot', password='ogrebot', email='ogrebot@example.com', active=False, roles=[]
        )
        db_session.add(ogrebot)
        db_session.commit()

        yield db_session

    # terminate any existing DB connections
    terminate_db_connections(engine, 'test')

    # cleanup the test mysql db
    run_query('drop database if exists test')


@pytest.yield_fixture(scope='function')
def postgresql(request, flask_app, _postgresql):
    """
    Function-scope fixture which rolls back any DB changes made during unit test
    """
    yield _postgresql
    Format.query.delete()
    Version.query.delete()
    Ebook.query.delete()


@pytest.fixture(scope='session')
def user(request, _postgresql):
    if request.config.getoption('--only-client'):
        return

    return _create_user(request, _postgresql)

@pytest.fixture(scope='session')
def user2(request, _postgresql):
    if request.config.getoption('--only-client'):
        return

    return _create_user(request, _postgresql)

def _create_user(request, _postgresql):
    # create random username
    username = ''.join(random.choice(string.ascii_lowercase) for n in range(6))
    # create user in auth DB
    _user = User(username, password=username, email='{}@example.com'.format(username), active=True, roles=[])
    _user.confirmed_at = datetime.datetime.utcnow()
    _user.preferred_ebook_format = 'mobi'
    _postgresql.add(_user)
    _postgresql.commit()
    return _user


@pytest.yield_fixture(scope='function')
def ogreclient_auth_token(_flask_app, user):
    client = _flask_app.test_client()
    result = client.post(
        '/login',
        data=json.dumps({'email': user.email, 'password': user.username}),
        content_type='application/json'
    )
    yield json.loads(result.data)['response']['user']['authentication_token']
    client.get('/logout')


@pytest.fixture
def client_sync(request):
    '''
    Wrap the ogreclient sync() function with another which provides a CliPrinter
    and captures all the output from the sync
    '''
    if request.config.getoption('--only-client'):
        return

    from ogreclient.ogreclient.core import sync
    from ogreclient.ogreclient.printer import CliPrinter

    # set printer to capture all logs
    prntr = CliPrinter.get_printer()
    CliPrinter.init(log_output=True)

    def wrapped(config):
        sync(config)
        return prntr.logs
    return wrapped


@pytest.fixture(scope='session')
def logger():
    logger = logging.getLogger('testing')
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.DEBUG)
    return logger


@pytest.yield_fixture(scope='function')
def s3bucket(app_config):
    s3 = connect_s3(app_config)
    try:
        bucket = s3.create_bucket(app_config['EBOOK_S3_BUCKET'])
    except boto.exception.S3CreateError:
        bucket = s3.get_bucket(app_config['EBOOK_S3_BUCKET'])
    yield bucket
    for k in bucket.list():
        k.delete()
    s3.delete_bucket(bucket)


@pytest.fixture(scope='session')
def cd():
    @contextlib.contextmanager
    def inner_cd(new_path):
        """ Context manager for changing the current working directory """
        saved_path = os.getcwd()
        try:
            os.chdir(new_path)
            yield new_path
        finally:
            os.chdir(saved_path)
    return inner_cd

@pytest.yield_fixture(scope='function')
def search(flask_app):
    search = Search(flask_app.whoosh, pagelen=100)
    yield search
    with flask_app.whoosh.writer() as writer:
        writer.mergetype = whoosh.writing.CLEAR


@pytest.fixture(scope='session')
def get_data_fixtures():
    """
    Load a set data fixtures for a particular test. Fixtures must be stored in:
        <test_filename>_fixtures/<testname>.yaml

    This YAML file should contain all fixtures for the test.
    """
    def wrapped(file_path, test_name):
        fixture_path = os.path.join(
            '{}_fixtures'.format(file_path[:-3]),
            '{}.yaml'.format(test_name.split('.')[-1:][0])
        )
        with open(fixture_path, 'r') as f:
            return yaml.load(f.read())
    return wrapped


@pytest.fixture(scope='function')
def ebook_fixture_azw3():
    return copy.deepcopy(fixtures.EBOOK_FIXTURE_1)


@pytest.fixture(scope='function')
def ebook_fixture_pdf():
    return copy.deepcopy(fixtures.EBOOK_FIXTURE_2)


@pytest.fixture(scope='function')
def ebook_fixture_epub():
    return copy.deepcopy(fixtures.EBOOK_FIXTURE_3)


@pytest.yield_fixture(scope='function')
def ebook_db_fixture_azw3(postgresql, ebook_fixture_azw3, user):
    ebook = ebook_store.create_ebook(
        "Andersen's Fairy Tales", 'H. C. Andersen', user, ebook_fixture_azw3
    )
    yield ebook
    postgresql.delete(ebook)
    postgresql.commit()


@pytest.yield_fixture(scope='function')
def ebook_db_fixture_pdf(postgresql, ebook_fixture_pdf, user):
    ebook = ebook_store.create_ebook(
        'Eggbert Yolker', 'The Sun is an Egg', user, ebook_fixture_pdf
    )
    yield ebook
    postgresql.delete(ebook)
    postgresql.commit()


@pytest.yield_fixture(scope='function')
def ebook_db_fixture_epub(postgresql, ebook_fixture_epub, user):
    ebook = ebook_store.create_ebook(
        'Foundation', 'Issac Asimov', user, ebook_fixture_epub
    )
    yield ebook
    postgresql.delete(ebook)
    postgresql.commit()


@pytest.fixture(scope='function')
def ebook_sync_fixture_1(ebook_fixture_azw3):
    return {
        "H. C.\u0006Andersen\u0007Andersen's Fairy Tales": ebook_fixture_azw3
    }


@pytest.fixture(scope='function')
def ebook_sync_fixture_2(ebook_fixture_pdf):
    return {
        'Eggbert\u0006Yolker\u0007The Sun is an Egg': ebook_fixture_pdf
    }
