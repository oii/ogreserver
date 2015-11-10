from __future__ import absolute_import
from __future__ import unicode_literals

from flask import current_app

import mock


def test_search(flask_app, datastore, user, rethinkdb, s3bucket, conversion):
    ebook_id = 'bcddb798'
    file_hash = '38b3fc3a'

    # create test ebook data directly in rethinkdb
    rethinkdb.table('ebooks').insert({
        'author': 'H. C. Andersen',
        'title': "Andersen's Fairy Tales",
        'ebook_id': ebook_id
    }).run()
    version_id = datastore._create_new_version(ebook_id, user.username, {
        'format': 'epub',
        'file_hash': file_hash,
        'size': 1234,
        'dedrm': False,
    })
    datastore.set_uploaded(file_hash, user.username, filename='egg.pub')

    with flask_app.app_context():
        # setup a fixture for expected call params to convert-ebook signal
        expected_params = [
            ((conversion,), {
                'ebook_id': ebook_id,
                'version_id': version_id,
                'original_filename': 'egg.pub',
                'dest_fmt': 'egg'
            }),
            ((conversion,), {
                'ebook_id': ebook_id,
                'version_id': version_id,
                'original_filename': 'egg.pub',
                'dest_fmt': 'mobi'
            }),
        ]

        # search for books which need converting; this sends convert signals
        conversion.search()

        # assert convert signal was sent twice, once for each missing format
        assert current_app.signals['convert-ebook'].send.call_count == 2
        assert current_app.signals['convert-ebook'].send.call_args_list == expected_params


def test_convert(flask_app, datastore, user, rethinkdb, s3bucket, conversion, mock_connect_s3,
                 mock_compute_md5, mock_subprocess_popen, mock_subprocess_check_call):
    ebook_id = 'bcddb798'
    converted_file_hash = 'new-file-hash'

    # create test ebook data directly in rethinkdb
    rethinkdb.table('ebooks').insert({
        'author': 'H. C. Andersen',
        'title': "Andersen's Fairy Tales",
        'ebook_id': ebook_id
    }).run()
    datastore._create_new_version(ebook_id, user.username, {
        'format': 'epub',
        'file_hash': '38b3fc3a',
        'size': 1234,
        'dedrm': False,
    })
    datastore.set_uploaded('38b3fc3a', user.username, filename='egg.pub')

    # mock return from Popen().communicate()
    mock_subprocess_popen.return_value.communicate.return_value = 'MOBI output written to', ''
    # mock subprocess.check_call
    mock_subprocess_check_call.return_value = None
    # mock compute_md5 to return preset file hash
    mock_compute_md5.return_value = (converted_file_hash, None)

    # mock ebook_write_metadata
    conversion.ebook_write_metadata = mock.MagicMock(name='method')

    # convert books; this starts store_ebook() tasks
    conversion.convert('bcddb798', 'fake-version-id', 'egg.pub', 'mobi')

    # assert connect_s3 was called
    mock_connect_s3.call_count == 1

    # assert ebook_write_metadata was called
    conversion.ebook_write_metadata.call_count == 1

    with flask_app.app_context():
        # assert celery store task was called
        current_app.signals['store-ebook'].send.assert_called_once_with(
            conversion,
            ebook_id='bcddb798',
            file_hash=converted_file_hash,
            fmt='mobi',
            username='ogrebot'
        )

    # verify new format object was created
    format_obj = rethinkdb.table('formats').get(converted_file_hash).run()
    assert format_obj is not None, 'format should exist with MD5 of {}'.format(converted_file_hash)
