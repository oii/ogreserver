from __future__ import absolute_import
from __future__ import unicode_literals

import mock


def test_search(datastore, user, rethinkdb, s3bucket, conversion):
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
    datastore.set_uploaded(file_hash, user.username)

    # search for books which need converting; this starts convert() tasks
    conversion.search()

    # assert convert task was called twice; for mobi & egg formats
    assert conversion.flask_app.signals['convert-ebook'].send.call_count == 2

    # assert convert-ebook signal call parameters
    expected_params = [
        ((conversion,), {
            'ebook_id': ebook_id,
            'version_id': version_id,
            'original_filename': datastore.generate_filename(file_hash),
            'dest_fmt': 'egg'
        }),
        ((conversion,), {
            'ebook_id': ebook_id,
            'version_id': version_id,
            'original_filename': datastore.generate_filename(file_hash),
            'dest_fmt': 'mobi'
        }),
    ]
    assert conversion.flask_app.signals['convert-ebook'].send.call_args_list == expected_params


def test_convert(datastore, user, rethinkdb, s3bucket, conversion, mock_connect_s3,
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

    # mock return from Popen().communicate()
    mock_subprocess_popen.return_value = mock.Mock()
    mock_subprocess_popen.return_value.communicate.return_value = 'MOBI output written to', ''
    # mock subprocess.check_call
    mock_subprocess_check_call.return_value = None
    # mock compute_md5 to return preset file hash
    mock_compute_md5.return_value = (converted_file_hash, None)

    # mock ebook_write_metadata
    conversion.ebook_write_metadata = mock.MagicMock(name='method')

    # convert books; this starts store_ebook() tasks
    conversion.convert(
        'bcddb798',
        'fake-version-id',
        datastore.generate_filename('38b3fc3a'),
        'mobi'
    )

    # assert connect_s3 was called
    mock_connect_s3.call_count == 1

    # assert ebook_write_metadata was called
    conversion.ebook_write_metadata.call_count == 1

    # assert celery store task was called
    conversion.flask_app.signals['store-ebook'].send.assert_called_once_with(
        conversion,
        ebook_id='bcddb798',
        file_hash=converted_file_hash,
        fmt='mobi',
        username='ogrebot'
    )

    # verify new format object was created
    format_obj = rethinkdb.table('formats').get(converted_file_hash).run()
    assert format_obj is not None, 'format should exist with MD5 of {}'.format(converted_file_hash)
