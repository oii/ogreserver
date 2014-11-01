from __future__ import unicode_literals

import collections

OGRESERVER_HOST = 'ogre.oii.yt'

# data structure:
#  is_valid_format (bool): sync to ogreserver
#  is_amazon_family (bool): an amazon-family format

EBOOK_FORMATS = collections.OrderedDict([
    ('mobi', [True,True]),
    ('azw', [True,True]),
    ('azw3', [True,True]),
    ('azw4', [True,True]),
    ('epub', [True,False]),
    ('azw1', [True,True]),
    ('tpz', [True,False]),
    ('pdb', [False,False,]),
    ('pdf', [False,False,]),
    ('lit', [False,False,]),
    ('html', [False,False]),
    ('zip', [False,False]),
])
