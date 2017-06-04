from __future__ import absolute_import
from __future__ import unicode_literals


def test_listing():
    pass


def test_listing_fragment():
    pass


def test_detail(flask_app, postgresql, user, ebook_db_fixture_azw3):
    '''
    Test /ebook/<ebook_id>/ endpoint
    '''
    client = flask_app.test_client()

    # spoof user auth
    with client.session_transaction() as sess:
        sess['user_id'] = user.id
        sess['_fresh'] = True

    result = client.get('/ebook/{}/'.format(ebook_db_fixture_azw3.id))
    assert result.status_code == 200


def test_set_curated():
    pass
