from __future__ import absolute_import
from __future__ import unicode_literals


def test_ranking1(amazon):
    response_items = [
        {'url': 'http://www.amazon.com/Unter-Dieben-Roman-German-Edition-ebook/dp/B0076Q1IH0', 'asin': 'B0076Q1IH0', 'title': 'Unter Dieben: Roman (German Edition)', 'author': 'Douglas Hulick'},
        {'url': 'http://www.amazon.com/Among-Thieves-Tale-Kin-Book/dp/B006RGFVXW', 'asin': 'B006RGFVXW', 'title': 'Among Thieves: A Tale of the Kin, Book 1', 'author': 'Douglas Hulick'}
    ]

    item = amazon._rank_results(response_items, 'Douglas Hulick Among Thieves (Tale of the Kin 1)')
    assert item['title'] == 'Among Thieves: A Tale of the Kin, Book 1'


def test_ranking2(amazon):
    response_items = [
        {'url': 'http://www.amazon.com/World-War-Oral-History-Zombie-ebook/dp/B000JMKQX0', 'asin': 'B000JMKQX0', 'title': 'World War Z: An Oral History of the Zombie War', 'author': 'Max Brooks'},
        {'url': 'http://www.amazon.com/World-War-Z-Italian-Edition-ebook/dp/B00DP48UGO', 'asin': 'B00DP48UGO', 'title': 'World War Z (Italian Edition)', 'author': 'Max Brooks'},
        {'url': 'http://www.amazon.com/The-Essential-Max-Brooks-Survival-ebook/dp/B00BVJG508', 'asin': 'B00BVJG508', 'title': 'The Essential Max Brooks: The Zombie Survival Guide and World War Z', 'author': 'Max Brooks'},
        {'url': 'http://www.amazon.com/Expert-Zombie-Hunters-Guide-Weapons-ebook/dp/B00FYAB1UE', 'asin': 'B00FYAB1UE', 'title': "The Expert Zombie Hunter's Guide to Weapons (The A to Z Weapons Guide for the Zombie World War)", 'author': 'Max Walker'},
        {'url': 'http://www.amazon.com/Operation-Zombie-l%C3%A4nger-sp%C3%A4ter-Edition-ebook/dp/B007A5MXX', 'asin': 'B007A5MXX', 'title': 'Operation Zombie: Wer l\xe4nger lebt, ist sp\xe4ter tot (German Edition)', 'author': 'Max Brooks'},
        {'url': 'http://www.amazon.com/LInt%C3%A9grale-survie-territoire-zombie-Edition-ebook/dp/B00N96BUH4', 'asin': 'B00N96BUH4', 'title': u"L'Int\xe9grale Z : World War Z + Guide de survie en territoire zombie (orbit) (French Edition)", 'author': 'Max Brooks'},
        {'url': 'http://www.amazon.com/Der-Zombie-Survival-Guide-%C3%9Cberleben-ebook/dp/B00XPE466W', 'asin': 'B00XPE466W', 'title': 'Der Zombie Survival Guide: \xdcberleben unter Untoten (German Edition)', 'author': 'Max Brooks'},
        {'url': 'http://www.amazon.com/Warm-Bodies-Novel-Series-Book-ebook/dp/B0043RSK3', 'asin': 'B0043RSK3', 'title': 'Warm Bodies: A Novel (The Warm Bodies Series Book 1)', 'author': 'Isaac Marion'},
        {'url': 'http://www.amazon.com/World-War-Amazing-Tidbits-GWhizBooks-com-ebook/dp/B00KN9C2DG', 'asin': 'B00KN9C2DG', 'title': "World War Z  - 101 Amazing Facts You Didn't Know: Fun Facts and Trivia Tidbits Quiz Game Books (GWhizBooks.com)", 'author': 'G Whiz'},
        {'url': 'http://www.amazon.com/World-War-Z-Operation-Zombie/dp/B00TBP63TW', 'asin': 'B00TBP63TW', 'title': 'World War Z: Operation Zombie', 'author': 'Max Brooks'}
    ]

    item = amazon._rank_results(response_items, 'Max Brooks World War Z')
    assert item['title'] == 'World War Z: An Oral History of the Zombie War'


def test_ranking3(amazon):
    response_items = [
        {'url': 'http://www.amazon.com/Altered-Carbon-Takeshi-Kovacs-Novels-ebook/dp/B000FBFMZ2', 'asin': 'B000FBFMZ2', 'title': 'Altered Carbon (Takeshi Kovacs Novels Book 1)', 'author': 'Richard K. Morgan'},
        {'url': 'http://www.amazon.com/Das-Unsterblichkeitsprogramm-Roman-German-Edition-ebook/dp/B004P1J3J4', 'asin': 'B004P1J3J4', 'title': 'Das Unsterblichkeitsprogramm: Roman (German Edition)', 'author': 'Richard Morgan'}
    ]

    item = amazon._rank_results(response_items, 'Richard Morgan Altered Carbon')
    assert item['title'] == 'Altered Carbon (Takeshi Kovacs Novels Book 1)'
