from __future__ import absolute_import
from __future__ import unicode_literals

import boto.exception
import mock
import os
import pytest
import yaml

from ogreserver.utils import connect_s3
from ogreserver.models.amazon import AmazonAPI
from ogreserver.models.goodreads import GoodreadsAPI


@pytest.yield_fixture(scope='function')
def s3bucket(app_config):
    s3 = connect_s3(app_config)
    try:
        bucket = s3.create_bucket(app_config['S3_BUCKET'])
    except boto.exception.S3CreateError:
        bucket = s3.get_bucket(app_config['S3_BUCKET'])
    yield bucket
    for k in bucket.list():
        k.delete()
    s3.delete_bucket(bucket)


@pytest.fixture(scope='function')
def amazon(app_config, logger):
    return AmazonAPI(
        logger,
        app_config.get('AWS_ADVERTISING_API_ACCESS_KEY', None),
        app_config.get('AWS_ADVERTISING_API_SECRET_KEY', None),
        app_config.get('AWS_ADVERTISING_API_ASSOCIATE_TAG', None),
    )

@pytest.yield_fixture(scope='function')
def mock_amazon():
    m = mock.patch('ogreserver.models.amazon.bottlenose.Amazon')
    yield m.start()
    m.stop()


@pytest.fixture(scope='session')
def goodreads(app_config, logger):
    return GoodreadsAPI(logger, app_config.get('GOODREADS_API_KEY', None))

@pytest.yield_fixture(scope='function')
def mock_goodreads():
    m = mock.patch('ogreserver.models.goodreads.requests')
    yield m.start()
    m.stop()


@pytest.yield_fixture(scope='function')
def mock_subprocess_popen(request):
    m = mock.patch('ogreserver.models.conversion.subprocess.Popen')
    yield m.start()
    m.stop()


@pytest.yield_fixture(scope='function')
def mock_subprocess_check_call(request):
    m = mock.patch('ogreserver.models.conversion.subprocess.check_call')
    yield m.start()
    m.stop()


@pytest.yield_fixture(scope='function')
def mock_connect_s3(request):
    m = mock.patch('ogreserver.models.conversion.connect_s3')
    yield m.start()
    m.stop()


@pytest.yield_fixture(scope='function')
def mock_compute_md5(request):
    m = mock.patch('ogreserver.models.conversion.compute_md5')
    yield m.start()
    m.stop()


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
