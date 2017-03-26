from __future__ import absolute_import
from __future__ import unicode_literals

import base64
import decimal
import hashlib
import random
import string

from flask import current_app as app

from ..models.user import User


def generate_ebook_id(author, title):
    """
    Generate the ebook_id from the author and title
    """
    return unicode(hashlib.md5(("~".join((author, title))).encode('utf8')).hexdigest())


def versions_rank_algorithm(quality, popularity):
    """
    Generate a score for this version of an ebook.

    The quality score and the popularity score are ratioed together 70:30
    Since popularity is a scalar and can grow indefinitely, it's divided by
    the number of total system users.

    Popularity is set to 10 when a newly decrypted ebook is added to OGRE
    Every download increases a version's popularity
    Every duplicate found on sync increases a version's popularity.
    """
    return (quality * decimal.Decimal(0.7)) + \
            (popularity / User.get_total_users() * 100 * decimal.Decimal(0.3))


def is_non_fiction(fmt):
    """
    Return list of formats classed as fiction
    """
    return fmt in [
        k for k,v in app.config['EBOOK_DEFINITIONS'].iteritems() if v.is_non_fiction is False
    ]


def compute_md5(filepath, buf_size=8192):
    """
    Adapted from boto/utils.py

    Compute MD5 hash on passed file and return results in a tuple of values.

    :type fp: file
    :param fp: File pointer to the file to MD5 hash.  The file pointer
    will be reset to the beginning of the file before the
    method returns.

    :type buf_size: integer
    :param buf_size: Number of bytes per read request.

    :rtype: tuple
    :return: A tuple containing the hex digest version of the MD5 hash
    as the first element, the base64 encoded version of the
    plain digest as the second element and the file size as
    the third element.
    """
    fp = open(filepath, "rb")
    try:
        m = hashlib.md5()
        fp.seek(0)
        s = fp.read(buf_size)
        while s:
            m.update(s)
            s = fp.read(buf_size)

        hex_md5 = m.hexdigest()
        base64md5 = base64.encodestring(m.digest())

        if base64md5[-1] == '\n':
            base64md5 = base64md5[0:-1]

        file_size = fp.tell()
        fp.seek(0)
        return (hex_md5, base64md5, file_size)
    finally:
        fp.close()


def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for x in range(size))
