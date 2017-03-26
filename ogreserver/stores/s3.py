from __future__ import absolute_import
from __future__ import unicode_literals

import re

from flask import current_app as app
from unidecode import unidecode

from . import ebooks as ebook_store
from ..models.ebook import Version, Format
from ..utils.s3 import connect_s3

from .. import exceptions


def upload_ebook(ebook_id, file_hash, filepath, user, content_type=None):
    """
    Store an ebook on S3
    """
    s3 = connect_s3(app.config)
    bucket = s3.get_bucket(app.config['EBOOK_S3_BUCKET'].format(app.config['env']))

    # generate a nice filename for this ebook
    filename = _generate_filename(file_hash)

    app.logger.debug('Generated filename {} for {}'.format(filename, file_hash))

    # create a new storage key
    k = bucket.new_key(filename)
    k.content_type = content_type

    # check if our file is already up on S3
    if k.exists() is True:
        metadata = k._get_remote_metadata()
        if 'x-amz-meta-ogre-key' in metadata and metadata['x-amz-meta-ogre-key'] == ebook_id:
            # if already exists, abort and flag as uploaded
            ebook_store.set_uploaded(file_hash, user, filename)
            return False

    try:
        # push file to S3
        k.set_contents_from_filename(
            filepath,
            headers={'x-amz-meta-ogre-key': ebook_id},
            md5=(file_hash,0)
        )
        app.logger.info('UPLOADED {} {}'.format(user.username, filename))

        # mark ebook as stored
        ebook_store.set_uploaded(file_hash, user, filename)

    except exceptions.S3ResponseError as e:
        raise exceptions.S3DatastoreError(
            'S3 upload checksum failed! {}'.format(file_hash), inner_excp=e
        )

    return True


def _generate_filename(file_hash, author=None, title=None, fmt=None):
    """
    Generate the filename for a book on its way to S3

    Author, title & format are loaded if they are not supplied
    """
    if author is not None and type(author) is not unicode:
        raise UnicodeWarning('Author must be unicode')
    if title is not None and type(title) is not unicode:
        raise UnicodeWarning('Title must be unicode')

    if author is None or title is None:
        format = Format.query.join(
            Format.version
        ).join(
            Version.ebook
        ).filter(
            Format.file_hash == file_hash
        ).one()
        author = format.version.ebook.author
        title = format.version.ebook.title
        fmt = format.format

    elif fmt is None:
        # load the file format for this book's hash
        fmt = Format.query.get(file_hash).format

    # transpose unicode for ASCII filenames
    author = unidecode(author)
    title = unidecode(title)

    # remove apostrophes & strip whitespace
    author = author.replace("'", '').strip()
    title = title.replace("'", '').strip()

    # only alphabet allowed in filename; replace all else with underscore
    authortitle = re.sub('[^a-zA-Z0-9~]', '_', '{}~~{}'.format(author, title))

    # replace multiple underscores with a single
    # replace double tilde between author & title with double underscore
    authortitle = re.sub('(~|_+)', '_', authortitle)

    return '{}.{}.{}'.format(authortitle, file_hash[0:8], fmt)


def get_ebook_download_url(ebook_id, version_id=None, fmt=None, user=None):
    """
    Generate a download URL for the requested ebook
    """
    # calculate the best ebook to return, based on the supplied params
    file_hash = ebook_store.get_best_ebook_filehash(ebook_id, version_id, fmt, user)

    # increase popularity on download
    ebook_store.increment_popularity(file_hash)

    # load the stored s3 filename
    format = Format.query.get(file_hash)

    # create an expiring auto-authenticate url for S3
    s3 = connect_s3(app.config)
    return s3.generate_url(
        app.config['DOWNLOAD_LINK_EXPIRY'],
        'GET',
        bucket=app.config['EBOOK_S3_BUCKET'].format(app.config['env']),
        key=format.s3_filename
    )
