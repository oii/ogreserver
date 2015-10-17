from __future__ import absolute_import
from __future__ import unicode_literals


def test_author_title_search1(amazon):
    # search author, title on Amazon
    am_data = amazon.search(author='ccc ccc', title='Lee, Harper--To Kill a Mockingbird')
    assert am_data is None


def test_author_title_search2(amazon):
    am_data = amazon.search(author='Richard Morgan', title='Black Man')
    assert am_data['asin'] == '2352942322'
    assert am_data['author'] == 'Richard Morgan'
    assert am_data['title'] == 'Black Man'
    assert am_data['image_url'] == 'http://ecx.images-amazon.com/images/I/51URUN95YpL.jpg'
    assert am_data['url'] == 'http://www.amazon.com/Black-Man-Richard-Morgan/dp/2352942322'


def test_author_title_search3(amazon):
    am_data = amazon.search(author='Max Brooks', title='World War Z')
    assert am_data['asin'] == 'B000JMKQX0'
    assert am_data['author'] == 'Max Brooks'
    assert am_data['title'] == 'World War Z: An Oral History of the Zombie War'
    assert am_data['image_url'] == 'http://ecx.images-amazon.com/images/I/51ELXqAe9UL.jpg'
    assert am_data['url'] == 'http://www.amazon.com/World-War-Oral-History-Zombie-ebook/dp/B000JMKQX0'


def test_author_title_search4(amazon):
    am_data = amazon.search(author='Richard Morgan', title='Altered Carbon (GOLLANCZ S.F.)')
    assert am_data['asin'] == 'B000FBFMZ2'
    assert am_data['author'] == 'Richard K. Morgan'
    assert am_data['title'] == 'Altered Carbon (Takeshi Kovacs Novels Book 1)'
    assert am_data['image_url'] == 'http://ecx.images-amazon.com/images/I/51hFNetqu5L.jpg'
    assert am_data['url'] == 'http://www.amazon.com/Altered-Carbon-Takeshi-Kovacs-Novels-ebook/dp/B000FBFMZ2'


def test_invalid_asin_search(amazon):
    # search for a Kindle ASIN; which will raise AmazonItemNotAccessibleError
    # and subsequently search by author/title
    am_data = amazon.search(asin='B003WE9TU8', author='Max Brooks', title='World War Z')
    assert am_data['asin'] == 'B000JMKQX0'
    assert am_data['author'] == 'Max Brooks'
    assert am_data['title'] == 'World War Z: An Oral History of the Zombie War'
    assert am_data['image_url'] == 'http://ecx.images-amazon.com/images/I/51ELXqAe9UL.jpg'
    assert am_data['url'] == 'http://www.amazon.com/World-War-Oral-History-Zombie-ebook/dp/B000JMKQX0'


def test_valid_asin_search(amazon):
    # search for a valid ASIN
    am_data = amazon.search(asin='B000JMKQX0')
    assert am_data['asin'] == 'B000JMKQX0'
    assert am_data['author'] == 'Max Brooks'
    assert am_data['title'] == 'World War Z: An Oral History of the Zombie War'
    assert am_data['image_url'] == 'http://ecx.images-amazon.com/images/I/51ELXqAe9UL.jpg'
    assert am_data['url'] == 'http://www.amazon.com/World-War-Oral-History-Zombie-ebook/dp/B000JMKQX0'
