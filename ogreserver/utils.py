from __future__ import absolute_import
from __future__ import unicode_literals

import base64
import contextlib
import datetime
import hashlib
import random
import re
import shutil
import string
import tempfile

import boto
import boto.s3
import boto.s3.connection

import rethinkdb as r

from flask import render_template as flask_render_template

from .forms.search import SearchForm


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


def connect_s3(config):
    """
    Connect to either AWS S3 or a local S3 proxy (for dev)
    """
    if config['DEBUG'] is True:
        # connect to s3proxy on 8880 in dev
        return boto.connect_s3(
            aws_access_key_id='identity',
            aws_secret_access_key='credential',
            host='127.0.0.1',
            port=8880,
            is_secure=False,
            calling_format=boto.s3.connection.OrdinaryCallingFormat()
        )

    else:
        # connect to AWS
        return boto.s3.connect_to_region(
            config['AWS_REGION'],
            aws_access_key_id=config['AWS_ACCESS_KEY_ID'],
            aws_secret_access_key=config['AWS_SECRET_ACCESS_KEY']
        )


def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for x in range(size))


@contextlib.contextmanager
def make_temp_directory():
    temp_dir = tempfile.mkdtemp()
    try:
        yield temp_dir
    except Exception as e:
        raise e
    finally:
        shutil.rmtree(temp_dir)


def encode_rql_dates(data):
    '''
    Convert all datetime.date and datetime.datetime objects to RqlTzinfo objects
    '''
    for k,v in data.items():
        if type(v) is dict:
            encode_rql_dates(v)
        elif type(v) is datetime.date or type(v) is datetime.datetime:
            if type(v) is datetime.date:
                v = datetime.datetime.combine(v, datetime.time())
            data[k] = r.iso8601('{}Z'.format(v.isoformat()))


def decode_rql_dates(data):
    '''
    Convert all RqlTzinfo objects to datetime.datetime objects
    '''
    for k,v in data.items():
        if type(v) is dict:
            decode_rql_dates(v)
        elif type(v) is datetime.datetime:
            data[k] = v.isoformat()


def request_wants_json(request):
    best = request.accept_mimetypes.best_match(['application/json', 'text/html'])
    return best == 'application/json' and \
        request.accept_mimetypes[best] > \
        request.accept_mimetypes['text/html']


def clean_string(string):
    '''
    Clean up strings:
     - remove any trailing brackets (and their content)
    '''
    curly_brackets = re.compile('\(.+?\)')
    square_brackets = re.compile('\[.+?\]')
    for regex in (curly_brackets, square_brackets):
        string = regex.sub('', string)
    return string.strip()


def render_template(template, **context):
    '''
    Wrap Flask's render_template() function to add SearchForm() to every rendered template
    '''
    if 'search_form' not in context:
        context['search_form'] = SearchForm(csrf_enabled=False)
    return flask_render_template(template, **context)
