from __future__ import absolute_import

import os
import pytest

# import ogreclient installed locally
#from ogreclient.cli import download_dedrm
#from ogreclient.core import authenticate, sync_with_server
#from ogreclient.printer import DummyPrinter


@pytest.mark.xfail
def test_duplicate(ogreserver, client_config, tmpdir):
    pass
    # setup ebook home for this test
    #client_config['ebook_home'] = tmpdir.strpath

    #prntr = DummyPrinter()

    ## setup a sync data object
    #data = {
    #    "Carroll, Lewis - Alice's Adventures in Wonderland": {
    #        'format': 'epub',
    #        'file_hash': '42344f0e247923fcb347c0e5de5fc762',
    #        'owner': 'test',
    #        'size': 69339,
    #    }
    #}

    #session_key = authenticate(client_config['host'], client_config['username'], client_config['password'])
    #response = sync_with_server(client_config, prntr, session_key, data)

    #assert len(response['ebooks_to_upload']) == 1
    #assert response['ebooks_to_update']['42344f0e247923fcb347c0e5de5fc762']['dupe'] is False

    ## 2) sync the same book and ensure duplicate registered
    #response = sync_with_server(client_config, prntr, session_key, data)
    #assert response['ebooks_to_update']['42344f0e247923fcb347c0e5de5fc762']['dupe'] is True


@pytest.mark.xfail
def test_update_ogre_id(ogreserver, client_config, tmpdir):
    '''
    test client/server interaction in add_ogre_id_to_ebook
    '''
    pass
