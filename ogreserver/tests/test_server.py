from __future__ import absolute_import

import pytest

from ..models.datastore import DataStore


@pytest.mark.xfail
def test_confirm_endpoint():
    pass


def test_update_book_md5(flask_app, datastore, user):
    ebooks_dict = {
        "H. C. Andersen - Andersen's Fairy Tales": {
            'format': 'epub',
            'file_md5': '38b3fc3a',
            'owner': 'mafro',
            'size': 139654
        },
    }

    # create the datastore and run a sync
    ds = DataStore(flask_app.config, flask_app.logger)
    ds.update_library(ebooks_dict, user)

    # check the object in formats table
    format_obj = datastore.db('test').table('formats').get('38b3fc3a').run()
    assert format_obj is not None, 'format should exist with MD5 of 38b3fc3a'

    # md5 is different after ogre_id written to metadata on client
    ret = ds.update_book_md5('38b3fc3a', 'egg')
    assert ret is True, 'update_book_md5() returned false'

    format_obj = datastore.db('test').table('formats').get('egg').run()
    assert format_obj is not None, 'format should have been updated to MD5 of egg'
