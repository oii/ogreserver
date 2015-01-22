from __future__ import absolute_import
from __future__ import unicode_literals

import os
import pytest
import shutil


@pytest.mark.integration
@pytest.mark.requires_calibre
def test_full_sync(ogreserver, rethinkdb, client_config, client_sync, tmpdir):
    test_ebooks = ('pg11.mobi', 'pg120.epub', 'DRM.azw')

    # copy test ebooks into test directory
    for filename in test_ebooks:
        shutil.copyfile(
            os.path.join('tests', 'ebooks', filename),
            os.path.join(tmpdir.strpath, filename),
        )

    # set ebook home test directory
    client_config['ebook_home'] = tmpdir.strpath

    # run ogreclient sync
    client_sync(client_config)
