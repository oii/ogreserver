from __future__ import absolute_import
from __future__ import unicode_literals

import os

import mock

from ogreserver.models.conversion import Conversion
from ogreserver.stores import ebooks as ebook_store


@mock.patch('ogreserver.models.conversion.make_temp_directory')
def test_search(mock_utils_make_tempdir, flask_app, postgresql, user, ebook_db_fixture_azw3):
    conversion = Conversion(flask_app.config)

    # mark test book as uploaded
    ebook_store.set_uploaded(
        ebook_db_fixture_azw3.versions[0].source_format.file_hash, user, filename='egg.pub'
    )

    # setup a fixture for expected call params to convert-ebook signal
    expected_params = [
        ((conversion,), {
            'ebook_id': ebook_db_fixture_azw3.id,
            'version_id': ebook_db_fixture_azw3.versions[0].id,
            'original_filename': 'egg.pub',
            'dest_fmt': 'egg'
        }),
        ((conversion,), {
            'ebook_id': ebook_db_fixture_azw3.id,
            'version_id': ebook_db_fixture_azw3.versions[0].id,
            'original_filename': 'egg.pub',
            'dest_fmt': 'mobi'
        }),
    ]

    # search for books which need converting; this sends convert signals
    conversion.search()

    # assert convert signal was sent twice, once for each missing format
    assert flask_app.signals['convert-ebook'].send.call_count == 2
    assert flask_app.signals['convert-ebook'].send.call_args_list == expected_params


@mock.patch('ogreserver.models.conversion.make_temp_directory')
def test_search_no_results_after_convert(mock_utils_make_tempdir, flask_app, postgresql, user, ebook_db_fixture_azw3):
    conversion = Conversion(flask_app.config)

    # mark test book as uploaded
    ebook_store.set_uploaded(
        ebook_db_fixture_azw3.versions[0].source_format.file_hash, user, filename='egg.pub'
    )

    # create extra formats mobi and egg for ebook_db_fixture_azw3
    ebook_store.create_format(ebook_db_fixture_azw3.versions[0], 'f7025dd7', 'mobi', user=user)
    ebook_store.create_format(ebook_db_fixture_azw3.versions[0], '96673ca3', 'egg', user=user)

    # search for books which need converting; this sends convert signals
    conversion.search()

    # assert convert signal was sent twice, once for each missing format
    assert flask_app.signals['convert-ebook'].send.call_count == 0


@mock.patch('ogreserver.models.conversion.make_temp_directory')
@mock.patch('ogreserver.models.conversion.shutil.move')
@mock.patch('ogreserver.models.conversion.connect_s3')
@mock.patch('ogreserver.models.conversion.subprocess.check_output')
@mock.patch('ogreserver.models.conversion.subprocess.check_call')
@mock.patch('ogreserver.models.conversion.subprocess.Popen')
def test_convert(mock_subprocess_popen, mock_subprocess_check_call,
                 mock_subprocess_check_output, mock_connect_s3, mock_shutil_move,
                 mock_utils_make_tempdir, flask_app, postgresql, user,
                 ebook_db_fixture_azw3):

    conversion = Conversion(flask_app.config)

    converted_file_hash = 'eggsbacon'
    target_convert_format = 'mobi'

    # mark test book as uploaded
    ebook_store.set_uploaded(
        ebook_db_fixture_azw3.versions[0].source_format.file_hash, user, filename='egg.pub'
    )

    # mock return from Popen().communicate()
    mock_subprocess_popen.return_value.communicate.return_value = 'MOBI output written to', ''
    # mock subprocess.check_call
    mock_subprocess_check_call.return_value = None

    # file_hash of the resulting converted file comes from _ebook_write_metadata()
    conversion._ebook_write_metadata = mock.Mock()
    conversion._ebook_write_metadata.return_value = converted_file_hash

    # NOTE: run the actual conversion code
    conversion.convert(
        ebook_db_fixture_azw3.id,
        ebook_db_fixture_azw3.versions[0],
        'tests/ebooks/pg11.epub',
        target_convert_format
    )

    # assert connect_s3 was called
    mock_connect_s3.call_count == 1

    # assert ebook_write_metadata was called
    conversion._ebook_write_metadata.call_count == 1

    # assert signal upload-ebook sent with correct args
    flask_app.signals['upload-ebook'].send.assert_called_once_with(
        conversion,
        ebook_id=ebook_db_fixture_azw3.id,
        filename=os.path.join(
            flask_app.config['UPLOADED_EBOOKS_DEST'],
            '{}.{}'.format(converted_file_hash, target_convert_format)
        ),
        file_hash=converted_file_hash,
        fmt=target_convert_format,
        username='ogrebot'
    )

    # verify new format object was created
    ebook = ebook_store.load_ebook_by_file_hash(converted_file_hash)
    assert ebook is not None, 'format should exist with MD5 of {}'.format(converted_file_hash)


@mock.patch('ogreserver.models.conversion.shutil.copy')
@mock.patch('ogreserver.models.conversion.compute_md5')
@mock.patch('ogreserver.models.conversion.subprocess.check_output')
def test_write_ebook_meta_epub(mock_subprocess_check_output, mock_compute_md5, mock_shutil_copy, flask_app, postgresql, user, ebook_db_fixture_epub):
    conversion = Conversion(flask_app.config)

    # mock compute_md5 to return preset file hash
    mock_compute_md5.return_value = ('eggsbacon', None)

    # ensure correct file_hash returned
    assert conversion._ebook_write_metadata(ebook_db_fixture_epub.id, 'fake.epub', 'epub') == 'eggsbacon'

    # ensure --identifier was called with ogre_id
    assert '--identifier ogre_id:{}'.format(ebook_db_fixture_epub.id) in mock_subprocess_check_output.call_args[0][0]


@mock.patch('ogreserver.models.conversion.shutil.copy')
@mock.patch('ogreserver.models.conversion.compute_md5')
@mock.patch('ogreserver.models.conversion.subprocess.check_output')
def test_write_ebook_meta_pdf(mock_subprocess_check_output, mock_compute_md5, mock_shutil_copy, flask_app, postgresql, user, ebook_db_fixture_pdf):
    conversion = Conversion(flask_app.config)

    # mock compute_md5 to return preset file hash
    mock_compute_md5.return_value = ('eggsbacon', None)

    # ensure correct file_hash returned
    assert conversion._ebook_write_metadata(ebook_db_fixture_pdf.id, 'fake.pdf', 'pdf') == 'eggsbacon'

    # ensure --tags was called with ogre_id
    assert '--tags ogre_id={}'.format(ebook_db_fixture_pdf.id) in mock_subprocess_check_output.call_args[0][0]
    assert 'tagged=' not in mock_subprocess_check_output.call_args[0][0]


@mock.patch('ogreserver.models.conversion.shutil.copy')
@mock.patch('ogreserver.models.conversion.compute_md5')
@mock.patch('ogreserver.models.conversion.subprocess.check_output')
def test_write_ebook_meta_azw3(mock_subprocess_check_output, mock_compute_md5, mock_shutil_copy, flask_app, postgresql, user, ebook_db_fixture_azw3):
    conversion = Conversion(flask_app.config)

    # mock compute_md5 to return preset file hash
    mock_compute_md5.return_value = ('eggsbacon', None)

    # ensure correct file_hash returned
    assert conversion._ebook_write_metadata(ebook_db_fixture_azw3.id, 'fake.mobi', 'mobi') == 'eggsbacon'

    # ensure --tags was called with ogre_id
    assert '--tags ogre_id={}'.format(ebook_db_fixture_azw3.id) in mock_subprocess_check_output.call_args[0][0]
    assert 'tagged=' not in mock_subprocess_check_output.call_args[0][0]


@mock.patch('ogreserver.models.conversion.shutil.copy')
@mock.patch('ogreserver.models.conversion.compute_md5')
@mock.patch('ogreserver.models.conversion.subprocess.check_output')
def test_write_ebook_meta_azw3_with_tags(mock_subprocess_check_output, mock_compute_md5, mock_shutil_copy, flask_app, postgresql, user, ebook_fixture_azw3):
    conversion = Conversion(flask_app.config)

    # include some tags in the source ebook fixture
    ebook_fixture_azw3['meta']['tags'] = 'tagged=bacon'

    # create test ebook data
    ebook = ebook_store.create_ebook(
        "Andersen's Fairy Tales", 'H. C. Andersen', user, ebook_fixture_azw3
    )

    # mock compute_md5 to return preset filtagged=bacone hash
    mock_compute_md5.return_value = ('eggsbacon', None)

    # ensure correct file_hash returned
    assert conversion._ebook_write_metadata(ebook.id, 'fake.mobi', 'mobi') == 'eggsbacon'

    # ensure --tags was called with ogre_idtagged=bacon
    assert '--tags ogre_id={}, tagged=bacon'.format(ebook.id) in mock_subprocess_check_output.call_args[0][0]
