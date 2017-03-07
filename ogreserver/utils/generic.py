from __future__ import unicode_literals

import contextlib
import re
import shutil
import tempfile


@contextlib.contextmanager
def make_temp_directory():
    temp_dir = tempfile.mkdtemp()
    try:
        yield temp_dir
    except Exception as e:
        raise e
    finally:
        shutil.rmtree(temp_dir)


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
