from __future__ import absolute_import
from __future__ import unicode_literals

import os
import pytest
import shutil

from ..ogreclient.ogreclient.providers import LibProvider


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

    # set ebook home for test
    client_config['ebook_home'] = tmpdir.strpath
    # .. and create ebook_home LibProvider (since we skip calling setup_ogreclient)
    ebook_home_provider = LibProvider(libpath=tmpdir.strpath)
    client_config['providers']['ebook_home'] = ebook_home_provider

    # run ogreclient sync
    client_sync(client_config)
