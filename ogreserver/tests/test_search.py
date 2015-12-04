from __future__ import absolute_import
from __future__ import unicode_literals


def test_search_keywords(search):
    '''
    Test a handful of keyword searches against author/title fields
    '''
    search.index_for_search({
        'ebook_id': 'ebad135',
        'author': 'Eggbert Robinson',
        'title': 'Deluded Visions of Bacon',
        'is_curated': True,
        'is_fiction': True,
    })

    # check author exact case-insensitive match
    result = search.query('eggbert')
    assert len(result['results']) == 1

    # check when both author & title fields in search string
    result = search.query('eggbert deluded')
    assert len(result['results']) == 1

    # check a random string fails
    result = search.query('zcsdsf')
    assert len(result['results']) == 0


def test_search_keyword_fuzzy(search):
    '''
    Test a fuzzy keyword search
    '''
    search.index_for_search({
        'ebook_id': 'ebad135',
        'author': 'Eggbert Robinson',
        'title': 'Deluded Visions of Bacon',
        'is_curated': True,
        'is_fiction': True,
    })

    # check author 1-char fuzzy match
    result = search.query('egbert')
    assert len(result['results']) == 1


def test_search_keyword_wildcard(search):
    '''
    Test a fuzzy keyword search
    '''
    search.index_for_search({
        'ebook_id': 'ebad135',
        'author': 'Eggbert Robinson',
        'title': 'Deluded Visions of Bacon',
        'is_curated': True,
        'is_fiction': True,
    })
    search.index_for_search({
        'ebook_id': 'c630bca',
        'author': 'Barry Eggleston',
        'title': 'Day of the Pig',
        'is_curated': True,
        'is_fiction': True,
    })

    # check wildcard works on author
    result = search.query('egg*')
    assert len(result['results']) == 2

    # check double wildcard
    result = search.query('*bin*')
    assert len(result['results']) == 1


def test_search_filters(search):
    search.index_for_search({
        'ebook_id': 'ebad135',
        'author': 'Eggbert Robinson',
        'title': 'Deluded Visions of Bacon',
        'is_curated': True,
        'is_fiction': True,
    })
    search.index_for_search({
        'ebook_id': 'c630bca',
        'author': 'Barry Eggleston',
        'title': 'Day of the Pig',
        'is_curated': False,
        'is_fiction': True,
    })
    search.index_for_search({
        'ebook_id': 'aef61e6',
        'author': 'Eggerston Benzo',
        'title': 'If Pigs Could Fly',
        'is_curated': False,
        'is_fiction': True,
    })

    # all books match egg*, but by default we only return is_curated=True
    result = search.query('egg*')
    assert len(result['results']) == 1

    # when filter is_curated=False applied, we return all books matching query
    result = search.query('egg*', is_curated=False)
    assert len(result['results']) == 3
