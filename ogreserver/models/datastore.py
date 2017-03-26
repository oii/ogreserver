from __future__ import absolute_import
from __future__ import unicode_literals

import datetime
import decimal
import hashlib
import re
import uuid

from boto.exception import S3ResponseError

import dateutil.parser
import ftfy

from flask import current_app as app, g
from sqlalchemy.orm import contains_eager

from .ebook import Ebook, Version, Format, SyncEvent
from .user import User
from ..utils.s3 import connect_s3

from ..exceptions import OgreException, BadMetaDataError, S3DatastoreError, \
        NoFormatAvailableError, SameHashSuppliedOnUpdateError, DuplicateBaseError, \
        FileHashDuplicateError, AuthortitleDuplicateError, AsinDuplicateError, IsbnDuplicateError


class DataStore():
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger


    def update_library(self, ebooks, user):
        """
        The core library synchronisation method.
        A dict containing ebook metadata and file hashes is sent by each client
        and synchronised against the contents of the OGRE database.
        """
        output = {}

        for authortitle, incoming in ebooks.items():
            try:
                # build output to return to client
                output[incoming['file_hash']] = {'new': False, 'update': False, 'dupe': False}

                # parse and cleanup incoming text
                author, title = DataStore._parse_and_sanitize(
                    authortitle, incoming['meta'], file_hash=incoming['file_hash'][0:7]
                )

                existing_ebook = None

                try:
                    # check for ogre_id from metadata passed as ebook_id
                    existing_ebook = self.load_ebook(incoming['ebook_id'])

                    # remove ebook_id from incoming metadata dict
                    del(incoming['ebook_id'])

                except KeyError as e:
                    # verify if this ebook_id already exists in the DB, but is not on the incoming ebook
                    existing_ebook = self.load_ebook(DataStore._generate_ebook_id(author, title))

                    # tell client to set ogre_id on this ebook
                    output[incoming['file_hash']]['update'] = True

                # check if this exact file has been uploaded before
                identical_ebook = self.load_ebook_by_file_hash(incoming['file_hash'])
                if identical_ebook:
                    raise FileHashDuplicateError(identical_ebook.id, incoming['file_hash'])

                else:
                    # check if original source ebook was uploaded with this hash
                    original_ebook = self.load_ebook_by_original_file_hash(incoming['file_hash'])

                    if original_ebook is not None:
                        raise FileHashDuplicateError(
                            original_ebook.id,
                            original_ebook.versions[0].source_format.file_hash
                        )

                if not existing_ebook:
                    # check for ASIN & ISBN duplicates
                    # the assumption is that ASIN dupes are the same book from the Amazon store
                    if 'asin' in incoming['meta']:
                        existing_ebook = self.load_ebook_by_asin(incoming['meta']['asin'])
                        if existing_ebook:
                            raise AsinDuplicateError(existing_ebook.id)

                    if 'isbn' in incoming['meta']:
                        existing_ebook = self.load_ebook_by_isbn(incoming['meta']['isbn'])
                        if existing_ebook:
                            raise IsbnDuplicateError(existing_ebook.id)

                    # check for author/title duplicates
                    existing_ebook = self.load_ebook_by_authortitle(author, title)

                    if existing_ebook:
                        # duplicate authortitle found
                        # must be a new version of the book else it would have been matched above
                        # don't accept new version of book from user who has already syncd it before
                        if existing_ebook.original_version.uploader is user:
                            raise AuthortitleDuplicateError(existing_ebook.id, incoming['file_hash'])

                    else:
                        # new books are easy
                        ebook = self.create_ebook(title, author, user, incoming)

                        # mark book as new
                        output[incoming['file_hash']]['ebook_id'] = ebook.id
                        output[incoming['file_hash']]['new'] = True
                        continue

                # create new version, with its initial format
                self.create_version(
                    existing_ebook,
                    user,
                    incoming['file_hash'],
                    incoming['format'],
                    incoming['size'],
                    incoming['dedrm'],
                )

                # mark with ebook_id and continue
                output[incoming['file_hash']]['ebook_id'] = existing_ebook.id


            except DuplicateBaseError as e:
                if e.file_hash:
                    # increase popularity of existing duplicate ebook
                    self.increment_popularity(e.file_hash)

                    # add the current user as an owner of this file
                    self.append_owner(e.file_hash, user)

                # enable client to update book with ebook_id
                output[incoming['file_hash']]['ebook_id'] = e.ebook_id

                # inform client of duplicate
                output[incoming['file_hash']]['dupe'] = True

            except OgreException as e:
                # log this and report back to client
                self.logger.info(e)
                output[incoming['file_hash']]['error'] = unicode(e).encode('utf8')

                # don't update on client for failed books
                output[incoming['file_hash']]['update'] = False

            except Exception as e:
                self.logger.error(e, exc_info=True)

                # don't update on client for failed books
                output[incoming['file_hash']]['update'] = False

        return output


    @staticmethod
    def _parse_and_sanitize(authortitle, metadata, file_hash=None):
        try:
            # derive author and title from the key
            author, title = authortitle.split('\u0007')
            firstname, lastname = author.split('\u0006')

            # sanitize incoming text
            title = ftfy.fix_text(title.strip())
            firstname = ftfy.fix_text(firstname.strip())
            lastname = ftfy.fix_text(lastname.strip())

            for k, v in metadata.iteritems():
                metadata[k] = ftfy.fix_text(v.strip())

        except Exception as e:
            raise BadMetaDataError("Bad meta data on {}: {}".format(
                file_hash,
                authortitle.replace('\u0007', ' ').replace('\u0006', ' ')
            ), e)

        # recombine firstname, lastname into author
        author = '{} {}'.format(firstname, lastname)
        return author, title


    @staticmethod
    def _generate_ebook_id(author, title):
        # generate the ebook_id from the author and title
        return unicode(hashlib.md5(("~".join((author, title))).encode('utf8')).hexdigest())


    def create_ebook(self, title, author, user, incoming):
        ebook_id = DataStore._generate_ebook_id(author, title)

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
            'is_non_fiction': self.is_non_fiction(incoming['format']),
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

        version = self.create_version(
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

        # TODO signal new ebook created (when running in flask context)
        app.signals['ebook-created'].send(ebook, ebook_id=ebook_id)

        return ebook

    def is_non_fiction(self, fmt):
        return fmt in [
            k for k,v in self.config['EBOOK_DEFINITIONS'].iteritems() if v.is_non_fiction is True
        ]


    def create_version(self, ebook, user, file_hash, fmt, size, dedrm):
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
            'ranking': DataStore.versions_rank_algorithm(1, popularity),
            'original_file_hash': file_hash,
        }
        version = Version(**new_version)
        version.ebook = ebook

        # create a new format
        format = self.create_format(
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


    def create_format(self, version, file_hash, fmt, user=None, dedrm=None, ogreid_tagged=False, nocommit=False):
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


    def append_ebook_metadata(self, ebook, provider, metadata):
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


    def append_owner(self, file_hash, user):
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


    @staticmethod
    def _load_ebook_query():
        return Ebook.query.join(
            Ebook.versions
        ).join(
            Version.formats
        ).options(
            contains_eager(Ebook.versions, Version.formats)
        )


    def load_ebook(self, ebook_id):
        """
        Load an ebook by id

        params:
            ebook_id: str
        """
        query = DataStore._load_ebook_query()

        return query.filter(Ebook.id == ebook_id).one_or_none()


    def load_ebook_by_asin(self, asin):
        """
        Load an ebook by the ASIN
        """
        return Ebook.query.filter_by(asin=asin).first()


    def load_ebook_by_isbn(self, isbn):
        """
        Load an ebook by the ISBN
        """
        return Ebook.query.filter_by(isbn=isbn).first()


    def set_curated(self, ebook_id, state):
        ebook = Ebook.query.get(ebook_id)
        ebook.curated = state
        g.db_session.add(ebook)
        g.db_session.commit()


    def load_ebook_by_file_hash(self, file_hash):
        """
        Load an ebook object by a Format file_hash PK.

        params:
            file_hash: str
        """
        query = DataStore._load_ebook_query()

        if len(file_hash) < 32:
            # query LIKE startswith
            query = query.filter(
                Format.file_hash.like('{}%'.format(file_hash))
            )
        else:
            query = query.filter(Format.file_hash == file_hash)

        return query.one_or_none()


    def load_ebook_by_original_file_hash(self, file_hash):
        """
        When an ebook is first uploaded, before OGRE has modified it at all, the file_hash
        is recorded. Load an ebook object by this field.

        params:
            file_hash: str
        """
        query = DataStore._load_ebook_query()

        return query.filter(Version.original_file_hash == file_hash).one_or_none()


    def load_ebook_by_authortitle(self, author, title):
        """
        Load an ebook by the author/title combination

        params:
            author: str
            title: str
        """
        query = DataStore._load_ebook_query()

        return query.filter(
            Ebook.author.ilike(author),
            Ebook.title.ilike(title)
        ).one_or_none()


    def find_missing_formats(self, fmt, limit=None):
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
        # select distinct version_id which have supplied format and is fiction
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
            Ebook.is_non_fiction == False
        ).filter(
            ~Version.id.in_(query.subquery())
        )

        if limit:
            query = query.limit(limit)

        return query.all()


    @staticmethod
    def versions_rank_algorithm(quality, popularity):
        """
        Generate a score for this version of an ebook

        The quality % score and the popularity score are ratioed together 70:30
        Since popularity is a scalar and can grow indefinitely, it's divided by
        the number of total system users

        Popularity is set to 10 when a newly decrypted ebook is added to OGRE
        Every download increases a version's popularity
        Every duplicate found on sync increases a version's popularity
        """
        return (quality * decimal.Decimal(0.7)) + \
                (popularity / User.get_total_users() * 100 * decimal.Decimal(0.3))


    def get_ebook_download_url(self, ebook_id, version_id=None, fmt=None, user=None):
        """
        Generate a download URL for the requested ebook
        """
        # calculate the best ebook to return, based on the supplied params
        file_hash = self._get_best_ebook_filehash(ebook_id, version_id, fmt, user)

        # increase popularity on download
        self.increment_popularity(file_hash)

        # load the stored s3 filename
        format = Format.query.get(file_hash)

        # create an expiring auto-authenticate url for S3
        s3 = connect_s3(self.config)
        return s3.generate_url(
            self.config['DOWNLOAD_LINK_EXPIRY'],
            'GET',
            bucket=self.config['EBOOK_S3_BUCKET'].format(app.config['env']),
            key=format.s3_filename
        )


    def _get_best_ebook_filehash(self, ebook_id, version_id=None, fmt=None, user=None):
        """
        Get the file_hash for most appropriate format based on supplied params

        If version=None, the top-ranked one is returned
        If format=None, the user-preferred format or first from EBOOK_FORMATS is returned
        """
        ebook = self.load_ebook(ebook_id)

        file_hash = None

        # setup the list of formats in preferred order
        preferred_formats = self.config['EBOOK_FORMATS']

        # if no specific format requested, supply user's preferred
        if fmt is None and user is not None and user.preferred_ebook_format is not None:
            # add user's preferred format as top option in formats list
            preferred_formats = [] + self.config['EBOOK_FORMATS']
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
                raise NoFormatAvailableError('No version with id {}'.format(version_id))

        # iterate preferred_formats, break on first match on this version
        for fmt in preferred_formats:
            file_hash = next((
                f.file_hash for f in version.formats if f.format == fmt and f.uploaded is True
            ), None)
            if file_hash is not None:
                break

        # if no file_hash, we have a problem
        if file_hash is None:
            raise NoFormatAvailableError('{} {} {} {}'.format(ebook_id, version_id, fmt, user))

        return file_hash


    def increment_popularity(self, file_hash):
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
        version.ranking = DataStore.versions_rank_algorithm(version.quality, version.popularity)

        g.db_session.add(version)
        g.db_session.commit()


    def update_ebook_hash(self, current_file_hash, updated_file_hash):
        """
        Update a format with a new filehash (which is the primary key)
        This is invoked when OGRE ebook_id is written to a book's metadata by
        ogreclient, this changing the ebook's filehash
        """
        if current_file_hash == updated_file_hash:
            raise SameHashSuppliedOnUpdateError(current_file_hash)

        # return if this file_hash has already been seen
        # TODO under what conditions does this happen?
        if Format.query.get(updated_file_hash):
            return True

        format = Format.query.get(current_file_hash)
        if format is None:
            self.logger.error('Format {} does not exist'.format(current_file_hash))
            return False

        # update the ebook format as tagged by the client (insert/delete since changing PK)
        format.file_hash = updated_file_hash
        format.ogreid_tagged = True
        g.db_session.add(format)
        g.db_session.commit()

        self.logger.debug('Updated {} to {} on {}'.format(
            current_file_hash, updated_file_hash, format.version_id)
        )

        return True

    def set_uploaded(self, file_hash, user, filename, isit=True):
        """
        Mark an ebook as having been uploaded to S3
        """
        format = Format.query.get(file_hash)
        format.uploaded = isit
        format.uploaded_by = user
        format.s3_filename = filename
        g.db_session.add(format)
        g.db_session.commit()

    def set_dedrm_flag(self, file_hash):
        """
        Mark a book as having had DRM removed
        """
        format = Format.query.get(file_hash)
        format.dedrm = True
        g.db_session.add(format)
        g.db_session.commit()


    def store_ebook(self, ebook_id, file_hash, filepath, user, content_type=None):
        """
        Store an ebook on S3
        """
        s3 = connect_s3(self.config)
        bucket = s3.get_bucket(self.config['EBOOK_S3_BUCKET'].format(app.config['env']))

        # generate a nice filename for this ebook
        filename = self._generate_filename(file_hash)

        self.logger.debug('Generated filename {} for {}'.format(filename, file_hash))

        # create a new storage key
        k = bucket.new_key(filename)
        k.content_type = content_type

        # check if our file is already up on S3
        if k.exists() is True:
            metadata = k._get_remote_metadata()
            if 'x-amz-meta-ogre-key' in metadata and metadata['x-amz-meta-ogre-key'] == ebook_id:
                # if already exists, abort and flag as uploaded
                self.set_uploaded(file_hash, user, filename)
                return False

        try:
            # push file to S3
            k.set_contents_from_filename(
                filepath,
                headers={'x-amz-meta-ogre-key': ebook_id},
                md5=(file_hash,0)
            )
            self.logger.info('UPLOADED {} {}'.format(user.username, filename))

            # mark ebook as stored
            self.set_uploaded(file_hash, user, filename)

        except S3ResponseError as e:
            raise S3DatastoreError(
                'S3 upload checksum failed! {}'.format(file_hash), inner_excp=e
            )

        return True


    def _generate_filename(self, file_hash, author=None, title=None, fmt=None):
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
        from unidecode import unidecode
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


    def get_missing_books(self, user=None):
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


    def log_event(self, user, syncd_books_count, new_books_count):
        """
        Add entries to a log every time a user syncs from ogreclient
        """
        event = SyncEvent(
            user=user,
            syncd_books_count=syncd_books_count,
            new_books_count=new_books_count,
            timestamp=datetime.datetime.now(),
        )
        g.db_session.add(event)
        g.db_session.commit()
