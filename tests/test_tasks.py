from __future__ import absolute_import
from __future__ import unicode_literals

from contextlib import contextmanager
import datetime

from flask import appcontext_pushed, g
import mock

from ogreserver.models.ebook import Ebook


@contextmanager
def inject_db_session(app, db_session):
    '''
    Inject the test SQLAlchemy Session into the Flask g object
    '''
    def _handler(sender, **kwargs):
        g.db_session = db_session
    with appcontext_pushed.connected_to(_handler, app):
        yield


@mock.patch('ogreserver.tasks.image_upload')
@mock.patch('ogreserver.tasks.GoodreadsAPI')
@mock.patch('ogreserver.tasks.AmazonAPI')
def test_query_ebook_metadata_amazon(mock_amazon_class, mock_goodreads_class, mock_image_upload, flask_app, postgresql, ebook_db_fixture_azw3):
    '''
    Test query_ebook_metadata task when only Amazon responds
    '''
    mock_amazon = mock_amazon_class.return_value = mock.Mock()
    mock_amazon.search.return_value = {
        'author': 'Monsieur Oeuf',
        'title': 'Frying Up',
        'asin': 'BXXX999999',
        'publication_date': datetime.date(2015, 7, 28),
        'image_url': 'http://example.com/egg.jpg',
    }

    mock_goodreads = mock_goodreads_class.return_value = mock.Mock()
    mock_goodreads.search.return_value = None

    # late import inside Flask app_context
    from ogreserver.tasks import query_ebook_metadata

    with inject_db_session(flask_app, postgresql):
        query_ebook_metadata(ebook_db_fixture_azw3.id)

    # assert image_upload task is started
    mock_image_upload.delay.assert_called_once_with(
        ebook_db_fixture_azw3.id,
        'http://example.com/egg.jpg'
    )

    # ensure all metadata applied to the Ebook object
    ebook = Ebook.query.get(ebook_db_fixture_azw3.id)
    assert ebook.author == 'Monsieur Oeuf'
    assert ebook.title == 'Frying Up'
    assert ebook.asin == 'BXXX999999'
    assert ebook.provider_metadata['amazon']['author'] == 'Monsieur Oeuf'
    assert ebook.provider_metadata['amazon']['title'] == 'Frying Up'
    assert ebook.provider_metadata['amazon']['asin'] == 'BXXX999999'
    assert ebook.provider_metadata['amazon']['publication_date'] == '2015-07-28'


@mock.patch('ogreserver.tasks.image_upload')
@mock.patch('ogreserver.tasks.GoodreadsAPI')
@mock.patch('ogreserver.tasks.AmazonAPI')
def test_query_ebook_metadata_goodreads(mock_amazon_class, mock_goodreads_class, mock_image_upload, flask_app, postgresql, ebook_db_fixture_azw3):
    '''
    Test query_ebook_metadata task when only Goodreads responds
    '''
    mock_goodreads = mock_goodreads_class.return_value = mock.Mock()
    mock_goodreads.search.return_value = {
        'authors': [
            {'name': 'Monsieur Oeuf'}
        ],
        'title': 'Frying Up',
        'isbn13': '1234567890123',
        'num_pages': 99,
        'average_rating': '4.1',
    }

    mock_amazon = mock_amazon_class.return_value = mock.Mock()
    mock_amazon.search.return_value = None

    # late import inside Flask app_context
    from ogreserver.tasks import query_ebook_metadata

    with inject_db_session(flask_app, postgresql):
        query_ebook_metadata(ebook_db_fixture_azw3.id)

    # ensure all metadata applied to the Ebook object
    ebook = Ebook.query.get(ebook_db_fixture_azw3.id)
    assert ebook.author == 'Monsieur Oeuf'
    assert ebook.title == 'Frying Up'
    assert ebook.isbn13 == '1234567890123'
    assert ebook.provider_metadata['goodreads']['authors'][0]['name'] == 'Monsieur Oeuf'
    assert ebook.provider_metadata['goodreads']['title'] == 'Frying Up'
    assert ebook.provider_metadata['goodreads']['isbn13'] == '1234567890123'
    assert ebook.provider_metadata['goodreads']['average_rating'] == '4.1'


def test_image_upload():
    pass


def test_index_for_search():
    pass


@mock.patch('ogreserver.tasks.s3_store')
@mock.patch('ogreserver.tasks.setup_db_session')
def test_upload_ebook(mock_setup_db, mock_s3_store, flask_app, user, ebook_db_fixture_azw3):
    # late import inside Flask app_context
    from ogreserver.tasks import upload_ebook

    upload_ebook(
        ebook_db_fixture_azw3.id,
        'egg.epub',
        ebook_db_fixture_azw3.original_version.source_format.file_hash,
        'azw3',
        user.username
    )
    assert mock_s3_store.upload_ebook.call_count == 1


@mock.patch('ogreserver.tasks.Conversion')
@mock.patch('ogreserver.tasks.setup_db_session')
def test_conversion_search(mock_setup_db, mock_conversion_class, flask_app):
    # mock the object created from the Conversion() constructor
    mock_conversion_class.return_value = mock_conversion = mock.Mock()

    # late import inside Flask app_context
    from ogreserver.tasks import conversion_search

    conversion_search()
    assert mock_conversion.search.call_count == 1
