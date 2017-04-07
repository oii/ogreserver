from __future__ import absolute_import
from __future__ import unicode_literals

import uuid

import dateutil.parser

from datadog import statsd
from flask import current_app as app, g
from sqlalchemy.orm import contains_eager

from ..models.ebook import Ebook, Version, Format
from ..models.user import User
from ..utils.ebooks import generate_ebook_id, is_non_fiction, versions_rank_algorithm

from .. import exceptions


def _load_ebook_query():
    return Ebook.query.join(
        Ebook.versions
    ).join(
        Version.formats
    ).options(
        contains_eager(Ebook.versions, Version.formats)
    )


@statsd.timed()
def load_ebook(ebook_id):
    """
    Load an ebook by id

    params:
        ebook_id: str
    """
    query = _load_ebook_query()

    return query.filter(Ebook.id == ebook_id).one_or_none()


@statsd.timed()
def load_ebook_by_file_hash(file_hash):
    """
    Load an ebook object by a Format file_hash PK.

    params:
        file_hash: str
    """
    query = _load_ebook_query()

    if len(file_hash) < 32:
        # query LIKE startswith
        query = query.filter(
            Format.file_hash.like('{}%'.format(file_hash))
        )
    else:
        query = query.filter(Format.file_hash == file_hash)

    return query.one_or_none()


@statsd.timed()
def load_ebook_by_original_file_hash(file_hash):
    """
    When an ebook is first uploaded, before OGRE has modified it at all, the file_hash
    is recorded. Load an ebook object by this field.

    params:
        file_hash: str
    """
    query = _load_ebook_query()

    return query.filter(Version.original_file_hash == file_hash).one_or_none()


@statsd.timed()
def load_ebook_by_authortitle(author, title):
    """
    Load an ebook by the author/title combination

    params:
        author: str
        title: str
    """
    query = _load_ebook_query()

    return query.filter(
        Ebook.author.ilike(author),
        Ebook.title.ilike(title)
    ).one_or_none()


@statsd.timed()
def append_ebook_metadata(ebook, provider, metadata):
    """
    Append new metadata into an ebook from one of our providers

    params:
        ebook: Ebook obj
        provider: str (either Amazon or Goodreads)
        metadata: dict
    """
    ebook.provider_metadata = {provider: metadata}
    g.db_session.add(ebook)
    g.db_session.commit()

    # signal ebook updated
    app.signals['ebook-updated'].send(ebook, ebook_id=ebook.id)


@statsd.timed()
def load_ebook_by_asin(asin):
    """
    Load an ebook by the ASIN
    """
    return Ebook.query.filter_by(asin=asin).first()


@statsd.timed()
def load_ebook_by_isbn(isbn):
    """
    Load an ebook by the ISBN
    """
    return Ebook.query.filter_by(isbn=isbn).first()


@statsd.timed()
def create_ebook(title, author, user, incoming):
    ebook_id = generate_ebook_id(author, title)

    publish_date = None

    # parse dates
    if 'publish_date' in incoming['meta']:
        publish_date = dateutil.parser.parse(incoming['meta']['publish_date'])

    def _init_curated(provider):
        if provider == 'Amazon Kindle':
            return True
        elif provider == 'Adobe Digital Editions':
            return True
        else:
            return False

    # create this as a new book
    new_book = {
        'id': ebook_id,
        'title': title,
        'author': author,
        'publisher': incoming['meta']['publisher'] if 'publisher' in incoming['meta'] else None,
        'publish_date': publish_date,
        'is_non_fiction': is_non_fiction(incoming['format']),
        'is_curated': _init_curated(incoming['meta']['source']),
        'isbn': incoming['meta']['isbn'] if 'isbn' in incoming['meta'] else None,
        'asin': incoming['meta']['asin'] if 'asin' in incoming['meta'] else None,
        'uri': incoming['meta']['uri'] if 'uri' in incoming['meta'] else None,
        'raw_tags': incoming['meta']['tags'] if 'tags' in incoming['meta'] else None,
        'source_provider': incoming['meta']['source'],
        'source_title': title,
        'source_author': author
    }
    ebook = Ebook(**new_book)

    version = create_version(
        ebook,
        user,
        incoming['file_hash'],
        incoming['format'],
        incoming['size'],
        incoming['dedrm'],
    )

    # store first version uploaded (separately to avoid SA circular dependency)
    ebook.original_version = version
    g.db_session.add(ebook)
    g.db_session.commit()

    # signal new ebook created (when running in flask context)
    app.signals['ebook-created'].send(ebook, ebook_id=ebook_id)

    return ebook


@statsd.timed()
def create_version(ebook, user, file_hash, fmt, size, dedrm):
    # default higher popularity if book has been decrypted by ogreclient;
    # due to better guarantee of provenance
    if dedrm:
        popularity = 10
    else:
        popularity = 1

    new_version = {
        'id': str(uuid.uuid4()),
        'uploader': user,
        'size': size,
        'popularity': popularity,
        'quality': 1,
        'ranking': versions_rank_algorithm(1, popularity),
        'original_file_hash': file_hash,
    }
    version = Version(**new_version)
    version.ebook = ebook

    # create a new format
    format = create_format(
        version,
        file_hash,
        fmt,
        user=user,
        dedrm=dedrm,
        nocommit=True,
    )

    # store Version & Format
    g.db_session.add(version)
    g.db_session.commit()

    # store FK to source format (separately to avoid SA circular dependency in ORM)
    version.source_format = format
    g.db_session.add(version)
    g.db_session.commit()

    return version


@statsd.timed()
def create_format(version, file_hash, fmt, user=None, dedrm=None, ogreid_tagged=False, nocommit=False):
    new_format = {
        'file_hash': file_hash,
        'format': fmt,
        'uploader': user if user is not None else User.ogrebot,
        'owners': [user if user is not None else User.ogrebot],
        'uploaded': False,
        'ogreid_tagged': ogreid_tagged,
        'dedrm': dedrm,
    }
    format = Format(**new_format)
    format.version = version

    if not nocommit:
        g.db_session.add(format)
        g.db_session.commit()

    return format


@statsd.timed()
def increment_popularity(file_hash):
    """
    Increase an ebook version's popularity by one. Popularity is stored against
    the version record.

    params:
        file_hash: str
    """
    version = Version.query.join(
        Version.formats
    ).filter_by(
        file_hash=file_hash
    ).first()

    # increment popularity
    version.popularity += 1

    # calculate new ranking
    version.ranking = versions_rank_algorithm(version.quality, version.popularity)

    g.db_session.add(version)
    g.db_session.commit()


@statsd.timed()
def append_owner(file_hash, user):
    """
    Append the current user to the list of owners of this particular file

    params:
        file_hash: str
        user: User object
    """
    format = Format.query.get(file_hash)
    format.owners.append(user)
    g.db_session.add(format)
    g.db_session.commit()


@statsd.timed()
def update_ebook_hash(current_file_hash, updated_file_hash):
    """
    Update a format with a new filehash (which is the primary key)
    This is invoked when OGRE ebook_id is written to a book's metadata by
    ogreclient, this changing the ebook's filehash
    """
    if current_file_hash == updated_file_hash:
        raise exceptions.SameHashSuppliedOnUpdateError(current_file_hash)

    # return if this file_hash has already been seen
    # TODO under what conditions does this happen?
    if Format.query.get(updated_file_hash):
        return True

    format = Format.query.get(current_file_hash)
    if format is None:
        #logger.error('Format {} does not exist'.format(current_file_hash))
        return False

    # update the ebook format as tagged by the client (insert/delete since changing PK)
    format.file_hash = updated_file_hash
    format.ogreid_tagged = True
    g.db_session.add(format)
    g.db_session.commit()

    app.logger.debug('Updated {} to {} on {}'.format(
        current_file_hash, updated_file_hash, format.version_id
    ))

    return True


@statsd.timed()
def set_uploaded(file_hash, user, filename, isit=True):
    """
    Mark an ebook as having been uploaded to S3
    """
    format = Format.query.get(file_hash)
    format.uploaded = isit
    format.uploaded_by = user
    format.s3_filename = filename
    g.db_session.add(format)
    g.db_session.commit()


@statsd.timed()
def set_dedrm_flag(file_hash):
    """
    Mark a book as having had DRM removed
    """
    format = Format.query.get(file_hash)
    format.dedrm = True
    g.db_session.add(format)
    g.db_session.commit()


@statsd.timed()
def set_curated(ebook_id, state):
    """
    Mark a book as OGRE community curated
    """
    ebook = Ebook.query.get(ebook_id)
    ebook.curated = state
    g.db_session.add(ebook)
    g.db_session.commit()


@statsd.timed()
def get_missing_books(user=None):
    """
    Query for books marked as not uploaded
    """
    # query the formats table for un-uploaded ebooks
    query = Format.query.with_entities(
        Format.file_hash
    ).join(
        Format.version
    ).filter(
        Format.uploaded == False
    )

    # filter by User
    if user:
        query = query.join(Format.owners).filter(User.id == user.id)

    return [f.file_hash for f in query.all()]


@statsd.timed()
def find_missing_formats(fmt, limit=None):
    """
    Find ebook versions missing supplied format. Ignores non-fiction ebooks.

    Each ebook should have several formats available for download (defined
    in config['EBOOK_FORMATS']). This method is called nightly by a celery
    task to ensure all expected formats are available.

    Objects are returned where supplied fmt is missing (ie, needs creating)

    params:
        fmt (str)   Required ebook format
        limit (int) Limit number of results returned
    return:
        list of Version objects
    """
    # select distinct version_id which have supplied format and is_fiction
    query = Format.query.with_entities(
        Format.version_id
    ).distinct(
        Format.version_id
    ).filter(
        Format.format == fmt
    )

    # get all Versions missing that format
    query = Version.query.join(
        Version.ebook
    ).filter(
        Ebook.is_non_fiction == True
    ).filter(
        ~Version.id.in_(query.subquery())
    )

    if limit:
        query = query.limit(limit)

    return query.all()


@statsd.timed()
def get_best_ebook_filehash(ebook_id, version_id=None, fmt=None, user=None):
    """
    Get the file_hash for most appropriate format based on supplied params

    If version=None, the top-ranked one is returned
    If format=None, the user-preferred format or first from EBOOK_FORMATS is returned
    """
    ebook = load_ebook(ebook_id)

    file_hash = None

    # setup the list of formats in preferred order
    preferred_formats = app.config['EBOOK_FORMATS']

    # if no specific format requested, supply user's preferred
    if fmt is None and user is not None and user.preferred_ebook_format is not None:
        # add user's preferred format as top option in formats list
        preferred_formats = [] + app.config['EBOOK_FORMATS']
        preferred_formats.remove(user.preferred_ebook_format)
        preferred_formats.insert(0, user.preferred_ebook_format)

    elif fmt is not None:
        # search only for a specific format
        preferred_formats = [fmt]

    # find the appropriate version
    if version_id is None:
        if fmt is None:
            # select top-ranked version (list always ordered by rank)
            version = ebook.versions[0]
        else:
            # iterate versions, break on first version which has the format we want
            for v in ebook.versions:
                for f in v.formats:
                    if f.format == fmt and f.uploaded is True:
                        version = v
                        break
                break
    else:
        version = next((v for v in ebook.versions if v.id == version_id), None)
        if version is None:
            raise exceptions.NoFormatAvailableError('No version with id {}'.format(version_id))

    # iterate preferred_formats, break on first match on this version
    for fmt in preferred_formats:
        file_hash = next((
            f.file_hash for f in version.formats if f.format == fmt and f.uploaded is True
        ), None)
        if file_hash is not None:
            break

    # if no file_hash, we have a problem
    if file_hash is None:
        raise exceptions.NoFormatAvailableError('{} {} {} {}'.format(ebook_id, version_id, fmt, user))

    return file_hash
