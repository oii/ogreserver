from __future__ import absolute_import
from __future__ import unicode_literals

import os

import mock

from ogreserver.models.conversion import Conversion
from ogreserver.stores import ebooks as ebook_store


def test_search(flask_app, postgresql, user, mock_utils_make_tempdir, ebook_db_fixture_azw3):
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


def test_convert(flask_app, postgresql, user, ebook_db_fixture_azw3, mock_connect_s3,
                 mock_subprocess_popen,  mock_subprocess_check_call, mock_shutil_move,
                 mock_utils_make_tempdir):
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


def test_write_ebook_meta_epub(flask_app, postgresql, user, ebook_db_fixture_epub, mock_compute_md5, mock_subprocess_check_output, mock_shutil_copy):
    conversion = Conversion(flask_app.config)

    # mock compute_md5 to return preset file hash
    mock_compute_md5.return_value = ('eggsbacon', None)

    # ensure correct file_hash returned
    assert conversion._ebook_write_metadata(ebook_db_fixture_epub.id, 'fake.epub', 'epub') == 'eggsbacon'

    # ensure --identifier was called with ogre_id
    assert '--identifier ogre_id:{}'.format(ebook_db_fixture_epub.id) in mock_subprocess_check_output.call_args[0][0]


def test_write_ebook_meta_pdf(flask_app, postgresql, user, ebook_db_fixture_pdf, mock_compute_md5, mock_subprocess_check_output, mock_shutil_copy):
    conversion = Conversion(flask_app.config)

    # mock compute_md5 to return preset file hash
    mock_compute_md5.return_value = ('eggsbacon', None)

    # ensure correct file_hash returned
    assert conversion._ebook_write_metadata(ebook_db_fixture_pdf.id, 'fake.pdf', 'pdf') == 'eggsbacon'

    # ensure --tags was called with ogre_id
    assert '--tags ogre_id={}'.format(ebook_db_fixture_pdf.id) in mock_subprocess_check_output.call_args[0][0]
    assert 'tagged=' not in mock_subprocess_check_output.call_args[0][0]


def test_write_ebook_meta_azw3(flask_app, postgresql, user, ebook_db_fixture_azw3, mock_compute_md5, mock_subprocess_check_output, mock_shutil_copy):
    conversion = Conversion(flask_app.config)

    # mock compute_md5 to return preset file hash
    mock_compute_md5.return_value = ('eggsbacon', None)

    # ensure correct file_hash returned
    assert conversion._ebook_write_metadata(ebook_db_fixture_azw3.id, 'fake.mobi', 'mobi') == 'eggsbacon'

    # ensure --tags was called with ogre_id
    assert '--tags ogre_id={}'.format(ebook_db_fixture_azw3.id) in mock_subprocess_check_output.call_args[0][0]
    assert 'tagged=' not in mock_subprocess_check_output.call_args[0][0]


def test_write_ebook_meta_azw3_with_tags(flask_app, postgresql, user, ebook_fixture_azw3, mock_compute_md5, mock_subprocess_check_output, mock_shutil_copy):
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
