from __future__ import absolute_import
from __future__ import unicode_literals

import os

import mock


def test_search(flask_app, datastore, postgresql, user, conversion, mock_utils_make_tempdir, ebook_fixture_azw3):
    # create test ebook data
    ebook = datastore.create_ebook(
        "Andersen's Fairy Tales", 'H. C. Andersen', user, ebook_fixture_azw3
    )
    datastore.set_uploaded(ebook_fixture_azw3['file_hash'], user, filename='egg.pub')

    # setup a fixture for expected call params to convert-ebook signal
    expected_params = [
        ((conversion,), {
            'ebook_id': ebook.id,
            'version_id': ebook.versions[0].id,
            'original_filename': 'egg.pub',
            'dest_fmt': 'egg'
        }),
        ((conversion,), {
            'ebook_id': ebook.id,
            'version_id': ebook.versions[0].id,
            'original_filename': 'egg.pub',
            'dest_fmt': 'mobi'
        }),
    ]

    # search for books which need converting; this sends convert signals
    conversion.search()

    # assert convert signal was sent twice, once for each missing format
    assert flask_app.signals['convert-ebook'].send.call_count == 2
    assert flask_app.signals['convert-ebook'].send.call_args_list == expected_params


def test_convert(flask_app, datastore, postgresql, user, conversion,
                 ebook_fixture_azw3, mock_connect_s3, mock_subprocess_popen,
                 mock_subprocess_check_call, mock_shutil_move, mock_utils_make_tempdir):
    converted_file_hash = 'eggsbacon'
    target_convert_format = 'mobi'

    # create test ebook data
    ebook = datastore.create_ebook(
        "Andersen's Fairy Tales", 'H. C. Andersen', user, ebook_fixture_azw3
    )
    datastore.set_uploaded(ebook_fixture_azw3['file_hash'], user, filename='egg.pub')

    # mock return from Popen().communicate()
    mock_subprocess_popen.return_value.communicate.return_value = 'MOBI output written to', ''
    # mock subprocess.check_call
    mock_subprocess_check_call.return_value = None

    # file_hash of the resulting converted file comes from _ebook_write_metadata()
    conversion._ebook_write_metadata = mock.Mock()
    conversion._ebook_write_metadata.return_value = converted_file_hash

    # NOTE: run the actual conversion code
    conversion.convert(
        ebook.id,
        ebook.versions[0],
        'tests/ebooks/pg11.epub',
        target_convert_format
    )

    # assert connect_s3 was called
    mock_connect_s3.call_count == 1

    # assert ebook_write_metadata was called
    conversion._ebook_write_metadata.call_count == 1

    # assert signal store-ebook sent with correct args
    flask_app.signals['store-ebook'].send.assert_called_once_with(
        conversion,
        ebook_id=ebook.id,
        filename=os.path.join(
            flask_app.config['UPLOADED_EBOOKS_DEST'],
            '{}.{}'.format(converted_file_hash, target_convert_format)
        ),
        file_hash=converted_file_hash,
        fmt=target_convert_format,
        username='ogrebot'
    )

    # verify new format object was created
    ebook = datastore.load_ebook_by_file_hash(converted_file_hash)
    assert ebook is not None, 'format should exist with MD5 of {}'.format(converted_file_hash)


def test_write_ebook_meta_epub(datastore, postgresql, conversion, user, ebook_fixture_epub, mock_compute_md5, mock_subprocess_check_output, mock_shutil_copy):
    # create test ebook data
    ebook = datastore.create_ebook(
        'Foundation', 'Isaac Asimove', user, ebook_fixture_epub
    )

    # mock compute_md5 to return preset file hash
    mock_compute_md5.return_value = ('eggsbacon', None)

    # ensure correct file_hash returned
    assert conversion._ebook_write_metadata(ebook.id, 'fake.epub', 'epub') == 'eggsbacon'

    # ensure --identifier was called with ogre_id
    assert '--identifier ogre_id:{}'.format(ebook.id) in mock_subprocess_check_output.call_args[0][0]


def test_write_ebook_meta_pdf(datastore, postgresql, conversion, user, ebook_fixture_pdf, mock_compute_md5, mock_subprocess_check_output, mock_shutil_copy):
    # create test ebook data
    ebook = datastore.create_ebook(
        'The Sun is an Egg', 'Eggbert Yolker', user, ebook_fixture_pdf
    )

    # mock compute_md5 to return preset file hash
    mock_compute_md5.return_value = ('eggsbacon', None)

    # ensure correct file_hash returned
    assert conversion._ebook_write_metadata(ebook.id, 'fake.pdf', 'pdf') == 'eggsbacon'

    # ensure --tags was called with ogre_id
    assert '--tags ogre_id={}'.format(ebook.id) in mock_subprocess_check_output.call_args[0][0]
    assert 'tagged=' not in mock_subprocess_check_output.call_args[0][0]


def test_write_ebook_meta_azw3(datastore, postgresql, conversion, user, ebook_fixture_azw3, mock_compute_md5, mock_subprocess_check_output, mock_shutil_copy):
    # create test ebook data
    ebook = datastore.create_ebook(
        "Andersen's Fairy Tales", 'H. C. Andersen', user, ebook_fixture_azw3
    )

    # mock compute_md5 to return preset file hash
    mock_compute_md5.return_value = ('eggsbacon', None)

    # ensure correct file_hash returned
    assert conversion._ebook_write_metadata(ebook.id, 'fake.mobi', 'mobi') == 'eggsbacon'

    # ensure --tags was called with ogre_id
    assert '--tags ogre_id={}'.format(ebook.id) in mock_subprocess_check_output.call_args[0][0]
    assert 'tagged=' not in mock_subprocess_check_output.call_args[0][0]


def test_write_ebook_meta_azw3_with_tags(datastore, postgresql, conversion, user, ebook_fixture_azw3, mock_compute_md5, mock_subprocess_check_output, mock_shutil_copy):
    # include some tags in the source ebook fixture
    ebook_fixture_azw3['meta']['tags'] = 'tagged=bacon'

    # create test ebook data
    ebook = datastore.create_ebook(
        "Andersen's Fairy Tales", 'H. C. Andersen', user, ebook_fixture_azw3
    )

    # mock compute_md5 to return preset filtagged=bacone hash
    mock_compute_md5.return_value = ('eggsbacon', None)

    # ensure correct file_hash returned
    assert conversion._ebook_write_metadata(ebook.id, 'fake.mobi', 'mobi') == 'eggsbacon'

    # ensure --tags was called with ogre_idtagged=bacon
    assert '--tags ogre_id={}, tagged=bacon'.format(ebook.id) in mock_subprocess_check_output.call_args[0][0]
