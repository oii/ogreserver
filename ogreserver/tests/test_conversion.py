from __future__ import absolute_import
from __future__ import unicode_literals

import os

import mock


def test_search(flask_app, datastore, user, rethinkdb, conversion, mock_utils_make_tempdir, ebook_fixture_azw3):
    # create test ebook data
    ebook_id = datastore._create_new_ebook(
        "Andersen's Fairy Tales", 'H. C. Andersen', user, ebook_fixture_azw3
    )
    datastore.set_uploaded(ebook_fixture_azw3['file_hash'], user, filename='egg.pub')

    ebook_data = datastore.load_ebook(ebook_id)

    # setup a fixture for expected call params to convert-ebook signal
    expected_params = [
        ((conversion,), {
            'ebook_id': ebook_id,
            'version_id': ebook_data['versions'][0]['version_id'],
            'original_filename': 'egg.pub',
            'dest_fmt': 'egg'
        }),
        ((conversion,), {
            'ebook_id': ebook_id,
            'version_id': ebook_data['versions'][0]['version_id'],
            'original_filename': 'egg.pub',
            'dest_fmt': 'mobi'
        }),
    ]

    # search for books which need converting; this sends convert signals
    conversion.search()

    # assert convert signal was sent twice, once for each missing format
    assert flask_app.signals['convert-ebook'].send.call_count == 2
    assert flask_app.signals['convert-ebook'].send.call_args_list == expected_params


def test_convert(flask_app, datastore, user, rethinkdb, conversion,
                 ebook_fixture_azw3, mock_connect_s3, mock_subprocess_popen,
                 mock_subprocess_check_call, mock_shutil_move, mock_utils_make_tempdir):
    converted_file_hash = 'eggsbacon'
    target_convert_format = 'mobi'

    # create test ebook data
    ebook_id = datastore._create_new_ebook(
        "Andersen's Fairy Tales", 'H. C. Andersen', user, ebook_fixture_azw3
    )
    datastore.set_uploaded(ebook_fixture_azw3['file_hash'], user, filename='egg.pub')

    ebook_data = datastore.load_ebook(ebook_id)

    # mock return from Popen().communicate()
    mock_subprocess_popen.return_value.communicate.return_value = 'MOBI output written to', ''
    # mock subprocess.check_call
    mock_subprocess_check_call.return_value = None

    # file_hash of the resulting converted file comes from _ebook_write_metadata()
    conversion._ebook_write_metadata = mock.Mock()
    conversion._ebook_write_metadata.return_value = converted_file_hash

    # NOTE: run the actual conversion code
    conversion.convert(ebook_id, ebook_data['versions'][0]['version_id'], 'tests/ebooks/pg11.epub', target_convert_format)

    # assert connect_s3 was called
    mock_connect_s3.call_count == 1

    # assert ebook_write_metadata was called
    conversion._ebook_write_metadata.call_count == 1

    # assert signal store-ebook sent with correct args
    flask_app.signals['store-ebook'].send.assert_called_once_with(
        conversion,
        ebook_id=ebook_id,
        filename=os.path.join(
            flask_app.config['UPLOADED_EBOOKS_DEST'],
            '{}.{}'.format(converted_file_hash, target_convert_format)
        ),
        file_hash=converted_file_hash,
        fmt=target_convert_format,
        username='ogrebot'
    )

    # verify new format object was created
    format_obj = rethinkdb.table('formats').get(converted_file_hash).run()
    assert format_obj is not None, 'format should exist with MD5 of {}'.format(converted_file_hash)


def test_write_ebook_meta_epub(conversion, mock_compute_md5, mock_subprocess_check_output, mock_shutil_copy):
    # mock compute_md5 to return preset file hash
    mock_compute_md5.return_value = ('eggsbacon', None)

    # mock out datastore entirely
    conversion.datastore = mock.Mock()
    conversion.datastore.load_ebook.return_value = {
        'ebook_id': 'nosefleas',
        'meta': {'raw_tags': None},
    }

    # ensure correct file_hash returned
    assert conversion._ebook_write_metadata('nosefleas', 'fake.epub', 'epub') == 'eggsbacon'

    # ensure --identifier was called with ogre_id
    assert '--identifier ogre_id:nosefleas' in mock_subprocess_check_output.call_args[0][0]


def test_write_ebook_meta_azw3(conversion, mock_compute_md5, mock_subprocess_check_output, mock_shutil_copy):
    # mock compute_md5 to return preset file hash
    mock_compute_md5.return_value = ('eggsbacon', None)

    # mock out datastore entirely
    conversion.datastore = mock.Mock()
    conversion.datastore.load_ebook.return_value = {
        'ebook_id': 'nosefleas',
        'meta': {'raw_tags': None},
    }

    # ensure correct file_hash returned
    assert conversion._ebook_write_metadata('nosefleas', 'fake.azw3', 'azw3') == 'eggsbacon'

    # ensure --tags was called with ogre_id
    assert '--tags ogre_id=nosefleas' in mock_subprocess_check_output.call_args[0][0]
    assert 'tagged=' not in mock_subprocess_check_output.call_args[0][0]


def test_write_ebook_meta_pdf(conversion, mock_compute_md5, mock_subprocess_check_output, mock_shutil_copy):
    # mock compute_md5 to return preset file hash
    mock_compute_md5.return_value = ('eggsbacon', None)

    # mock out datastore entirely
    conversion.datastore = mock.Mock()
    conversion.datastore.load_ebook.return_value = {
        'ebook_id': 'nosefleas',
        'meta': {'raw_tags': None},
    }

    # ensure correct file_hash returned
    assert conversion._ebook_write_metadata('nosefleas', 'fake.pdf', 'pdf') == 'eggsbacon'

    # ensure --tags was called with ogre_id
    assert '--tags ogre_id=nosefleas' in mock_subprocess_check_output.call_args[0][0]
    assert 'tagged=' not in mock_subprocess_check_output.call_args[0][0]


def test_write_ebook_meta_mobi(conversion, mock_compute_md5, mock_subprocess_check_output, mock_shutil_copy):
    # mock compute_md5 to return preset file hash
    mock_compute_md5.return_value = ('eggsbacon', None)

    # mock out datastore entirely
    conversion.datastore = mock.Mock()
    conversion.datastore.load_ebook.return_value = {
        'ebook_id': 'nosefleas',
        'meta': {'raw_tags': None},
    }

    # ensure correct file_hash returned
    assert conversion._ebook_write_metadata('nosefleas', 'fake.mobi', 'mobi') == 'eggsbacon'

    # ensure --tags was called with ogre_id
    assert '--tags ogre_id=nosefleas' in mock_subprocess_check_output.call_args[0][0]
    assert 'tagged=' not in mock_subprocess_check_output.call_args[0][0]


def test_write_ebook_meta_mobi_with_tags(conversion, mock_compute_md5, mock_subprocess_check_output, mock_shutil_copy):
    # mock compute_md5 to return preset file hash
    mock_compute_md5.return_value = ('eggsbacon', None)

    # mock out datastore entirely
    conversion.datastore = mock.Mock()
    conversion.datastore.load_ebook.return_value = {
        'ebook_id': 'nosefleas',
        'meta': {'raw_tags': 'tagged=bacon'},
    }

    # ensure correct file_hash returned
    assert conversion._ebook_write_metadata('nosefleas', 'fake.mobi', 'mobi') == 'eggsbacon'

    # ensure --tags was called with ogre_id
    assert '--tags ogre_id=nosefleas, tagged=bacon' in mock_subprocess_check_output.call_args[0][0]
