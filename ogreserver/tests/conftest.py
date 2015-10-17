from __future__ import absolute_import
from __future__ import unicode_literals

import boto.exception
import mock
import pytest

from ..utils import connect_s3
from ..models.amazon import AmazonAPI
from ..models.goodreads import GoodreadsAPI


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


@pytest.fixture(scope='session')
def amazon(app_config, logger):
    return AmazonAPI(
        logger,
        app_config.get('AWS_ADVERTISING_API_ACCESS_KEY', None),
        app_config.get('AWS_ADVERTISING_API_SECRET_KEY', None),
        app_config.get('AWS_ADVERTISING_API_ASSOCIATE_TAG', None),
    )


@pytest.fixture(scope='session')
def goodreads(app_config, logger):
    return GoodreadsAPI(logger, app_config.get('GOODREADS_API_KEY', None))


@pytest.yield_fixture(scope='function')
def mock_subprocess_popen(request):
    m = mock.patch('ogre.ogreserver.models.conversion.subprocess.Popen')
    yield m.start()
    m.stop()


@pytest.yield_fixture(scope='function')
def mock_subprocess_check_call(request):
    m = mock.patch('ogre.ogreserver.models.conversion.subprocess.check_call')
    yield m.start()
    m.stop()


@pytest.yield_fixture(scope='function')
def mock_connect_s3(request):
    m = mock.patch('ogre.ogreserver.models.conversion.connect_s3')
    yield m.start()
    m.stop()


@pytest.yield_fixture(scope='function')
def mock_compute_md5(request):
    m = mock.patch('ogre.ogreserver.models.conversion.compute_md5')
    yield m.start()
    m.stop()
