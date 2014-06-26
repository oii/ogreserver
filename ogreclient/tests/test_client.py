from __future__ import absolute_import

import os
import shutil

from ogreclient.core import search_for_ebooks
from ogreclient.printer import DummyPrinter


def test_search(client_config, ebook_lib_path, tmpdir):
    # setup ebook home for this test
    client_config['ebook_home'] = tmpdir.strpath

    # stick Alice in Wonderland into ebook_home
    shutil.copy(os.path.join(ebook_lib_path, 'pg11.epub'), client_config['ebook_home'])

    # search for ebooks
    data = search_for_ebooks(client_config, prntr=DummyPrinter())

    # verify found book
    assert len(data) == 1
    assert data.keys()[0] == "Lewis Carroll - Alice's Adventures in Wonderland"
    assert data[data.keys()[0]]['file_hash'] == '42344f0e247923fcb347c0e5de5fc762'
