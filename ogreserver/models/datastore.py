from __future__ import absolute_import
from __future__ import unicode_literals

import hashlib
import re

import rethinkdb as r
from rethinkdb.errors import RqlRuntimeError

import boto
from boto.exception import S3ResponseError

import ftfy

from flask import current_app

from .user import User
from ..utils import connect_s3, encode_rql_dates

from ..exceptions import OgreException, BadMetaDataError, S3DatastoreError, RethinkdbError, \
        NoFormatAvailableError, SameHashSuppliedOnUpdateError, DuplicateBaseError, FileHashDuplicateError, \
        AuthortitleDuplicateError, AsinDuplicateError


class DataStore():
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger

        # connect rethinkdb and make default connection
        r.connect(db=self.config['RETHINKDB_DATABASE']).repl()


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

                existing_ebook = None

                try:
                    # check for ogre_id from metadata passed as ebook_id
                    existing_ebook = self.load_ebook(incoming['ebook_id'])

                    # remove ebook_id from incoming metadata dict
                    del(incoming['ebook_id'])

                except KeyError as e:
                    # tell client to set ogre_id on this ebook
                    output[incoming['file_hash']]['update'] = True


                # check if this exact file has been uploaded before
                if r.table('formats').get(incoming['file_hash']).run():
                    if existing_ebook is not None:
                        raise FileHashDuplicateError(existing_ebook['ebook_id'], incoming['file_hash'])
                    else:
                        ebook = self.load_ebook_by_file_hash(incoming['file_hash'])
                        raise FileHashDuplicateError(ebook['ebook_id'], incoming['file_hash'])

                else:
                    # check if original source ebook was uploaded with this hash
                    original_ebook = next(
                        r.table('versions').get_all(
                            incoming['file_hash'], index='original_filehash'
                        ).eq_join(
                            'version_id', r.table('formats'), index='version_id'
                        ).zip().run(), None
                    )

                    if original_ebook is not None:
                        raise FileHashDuplicateError(
                            original_ebook['ebook_id'],
                            original_ebook['file_hash']
                        )

                # check for ASIN duplicates
                # the assumption is that ASIN dupes are the same book from the Amazon store
                # they will ALWAYS have different file_hashes due to decryption of every file
                if 'asin' in incoming['meta']:
                    existing_ebook = next(r.table('ebooks').get_all(incoming['meta']['asin'], index='asin').run(), None)
                    if existing_ebook is not None:
                        raise AsinDuplicateError(existing_ebook['ebook_id'])

                # check for ISBN duplicates
                # these are treated as new versions of an existing ebook
                if 'isbn' in incoming['meta']:
                    existing_ebook = next(r.table('ebooks').get_all(incoming['meta']['isbn'], index='isbn').run(), None)

                try:
                    # derive author and title from the key
                    author, title = authortitle.split('\u0007')
                    firstname, lastname = author.split('\u0006')

                    # sanitize incoming text
                    for value in (title, firstname, lastname):
                        value = ftfy.fix_text(value.strip())

                    for _, value in incoming['meta'].iteritems():
                        value = ftfy.fix_text(value.strip())

                except Exception as e:
                    raise BadMetaDataError("Bad meta data on {}: {}".format(
                        incoming['file_hash'][0:7],
                        authortitle.replace('\u0007', ' ').replace('\u0006', ' ')
                    ), e)

                # recombine firstname, lastname into author
                author = '{} {}'.format(firstname, lastname)


                if not existing_ebook:
                    # check for author/title duplicates
                    existing_ebook = next(
                        r.table('ebooks').get_all(
                            [author.lower(), title.lower()],
                            index='authortitle'
                        ).run(), None
                    )

                    if existing_ebook:
                        # duplicate authortitle found
                        # must be a new version of the book else it would have been matched above
                        # don't accept new version of book from user who has already syncd it before
                        duplicate = next(
                            r.table('versions').get_all(
                                [existing_ebook['ebook_id'], user.username],
                                index='ebook_username'
                            ).run(), None
                        )

                        if duplicate:
                            raise AuthortitleDuplicateError(existing_ebook['ebook_id'], incoming['file_hash'])

                    else:
                        # new books are easy
                        ebook_id = self._create_new_ebook(title, author, user, incoming)

                        # mark book as new
                        output[incoming['file_hash']]['ebook_id'] = ebook_id
                        output[incoming['file_hash']]['new'] = True
                        continue

                # create new version, with its initial format
                self._create_new_version(existing_ebook['ebook_id'], user.username, incoming)

                # mark with ebook_id and continue
                output[incoming['file_hash']]['ebook_id'] = existing_ebook['ebook_id']


            except DuplicateBaseError as e:
                if e.file_hash:
                    # increase popularity on incoming duplicate ebook
                    self.increment_popularity(e.file_hash)

                    # add the current user as an owner of this file
                    self.append_owner(e.file_hash, user.username)

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


    def _create_new_ebook(self, title, author, user, incoming):
        # generate the ebook_id from the author and title
        ebook_id = unicode(hashlib.md5(("~".join((author, title))).encode('UTF-8')).hexdigest())

        # create this as a new book
        new_book = {
            'ebook_id': ebook_id,
            'title': title,
            'author': author,
            'rating': None,
            'comments': [],
            'publisher': incoming['meta']['publisher'] if 'publisher' in incoming['meta'] else None,
            'publish_date': incoming['meta']['publish_date'] if 'publish_date' in incoming['meta'] else None,
            'is_fiction': self.is_fiction(incoming['format']),
            'meta': {
                'isbn': incoming['meta']['isbn'] if 'isbn' in incoming['meta'] else None,
                'asin': incoming['meta']['asin'] if 'asin' in incoming['meta'] else None,
                'uri': incoming['meta']['uri'] if 'uri' in incoming['meta'] else None,
                'raw_tags': incoming['meta']['tags'] if 'tags' in incoming['meta'] else None,
                'source': {
                    'provider': incoming['meta']['source'],
                    'title': title,
                    'author': author
                }
            },
        }
        ret = r.table('ebooks').insert(new_book).run()
        if 'first_error' in ret:
            raise RethinkdbError(ret['first_error'])

        # create version and initial format
        version_id = self._create_new_version(ebook_id, user.username, incoming)

        # record the original file_hash of the originally supplied ebook
        ret = r.table('versions').get(version_id).update({
            'original_filehash': incoming['file_hash']
        }).run()
        if 'first_error' in ret:
            raise RethinkdbError(ret['first_error'])

        # signal new ebook created (when running in flask context)
        current_app.signals['ebook-created'].send(self, ebook_data=new_book)
        return ebook_id


    def _create_new_version(self, ebook_id, username, incoming):
        # default higher popularity if book has been decrypted by ogreclient;
        # due to better guarantee of provenance
        if incoming['dedrm']:
            popularity = 10
        else:
            popularity = 1

        # add the first version
        ret = r.table('versions').insert({
            'ebook_id': ebook_id,
            'user': username,
            'size': incoming['size'],
            'popularity': popularity,
            'quality': 1,
            'ranking': DataStore.versions_rank_algorithm(1, popularity),
            'original_format': incoming['format'],
            'date_added': r.now(),
        }).run()
        if 'first_error' in ret:
            raise RethinkdbError(ret['first_error'])

        # create a new format
        self._create_new_format(
            ret['generated_keys'][0],
            incoming['file_hash'],
            incoming['format'],
            username=username,
            dedrm=incoming['dedrm'],
        )
        return ret['generated_keys'][0]


    def _create_new_format(self, version_id, file_hash, fmt, username=None, dedrm=None, ogreid_tagged=False):
        ret = r.table('formats').insert({
            'file_hash': file_hash,
            'version_id': version_id,
            'format': fmt,
            'owners': [username if username is not None else 'ogrebot'],
            'uploaded_by': None,
            'uploaded': False,
            'is_fiction': self.is_fiction(fmt),
            'ogreid_tagged': ogreid_tagged,
            'dedrm': dedrm,
        }).run()
        if 'first_error' in ret:
            raise RethinkdbError(ret['first_error'])


    def is_fiction(self, fmt):
        return fmt in [
            k for k,v in self.config['EBOOK_DEFINITIONS'].iteritems() if v.is_non_fiction is False
        ]


    def update_ebook(self, ebook_id, data):
        """
        Update a part of an ebook record
        """
        # convert datetime objects for rethinkdb
        encode_rql_dates(data)

        ret = r.table('ebooks').get(ebook_id).update(data).run()
        if 'first_error' in ret:
            raise RethinkdbError(ret['first_error'])

        # signal ebook updated
        current_app.signals['ebook-updated'].send(self, ebook_id=ebook_id)


    def append_owner(self, file_hash, username):
        """
        Append the current user to the list of owners of this particular file
        """
        r.table('formats').get(file_hash).update(
            {'owners': r.row['owners'].set_insert(username)}
        ).run()


    def load_ebook(self, ebook_id):
        # query returns dict with ebook->versions->formats nested document
        # versions are ordered by popularity
        try:
            ebook = r.table('ebooks').get(ebook_id).merge(
                lambda ebook: {
                    'versions': r.table('versions').get_all(
                        ebook['ebook_id'], index='ebook_id'
                    ).order_by(
                        r.desc('ranking')
                    ).coerce_to('array').merge(
                        lambda version: {
                            'formats': r.table('formats').get_all(
                                version['version_id'], index='version_id'
                            ).coerce_to('array')
                        }
                    )
                }
            ).run()

        except RqlRuntimeError as e:
            if 'Cannot perform merge on a non-object non-sequence `null`' in str(e):
                return None
            else:
                raise e

        return ebook


    def load_ebook_by_file_hash(self, file_hash, match=False):
        # enable substring filehash searching; like git commit ids
        if match:
            filter_func = lambda d: d['file_hash'].match('^{}'.format(file_hash))
        else:
            filter_func = {'file_hash': file_hash}

        ebook_id = next(
            r.table('formats').filter(filter_func).eq_join(
                'version_id', r.table('versions'), index='version_id'
            ).zip().pluck(
                'ebook_id'
            )['ebook_id'].run(), None
        )

        if ebook_id is not None:
            # now return the full ebook object
            return self.load_ebook(ebook_id)


    def find_missing_formats(self, fmt, limit=None):
        """
        Find ebook versions missing supplied format. Ignores non-fiction ebooks.

        Each ebook should have several formats available for download (defined
        in config['EBOOK_FORMATS']). This method is called nightly by a celery
        task to ensure all defined formats are available.

        Objects are returned where supplied fmt is missing (ie, needs creating)

        Params:
            fmt (str)   Required ebook format that might be missing
            limit (int) Limit number of results returned
        Returns
            version_id: [
                {format, original_format, file_hash, ebook_id, s3_filename, uploaded},
                ...
            ]
        """
        q = r.table('formats').group(index='version_id').filter({'is_fiction': True}).filter(
            lambda row: r.table('formats').filter(
                {'format': fmt}
            )['version_id'].contains(
                row['version_id']
            ).not_()
        ).eq_join(
            'version_id', r.table('versions'), index='version_id'
        ).zip().pluck(
            'format', 'original_format', 'file_hash', 'ebook_id', 's3_filename', 'uploaded'
        )
        if limit:
            q = q.limit(limit)
        return q.run()


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
        return (quality * 0.7) + (float(popularity) / User.get_total_users() * 100 * 0.3)


    def get_ebook_download_url(self, ebook_id, version_id=None, fmt=None, user=None):
        """
        Generate a download URL for the requested ebook
        """
        # calculate the best ebook to return, based on the supplied params
        file_hash = self._get_best_ebook_filehash(ebook_id, version_id, fmt, user)

        # increase popularity on download
        self.increment_popularity(file_hash)

        # load the stored s3 filename
        filename = r.table('formats').get(file_hash)['s3_filename'].run()

        # create an expiring auto-authenticate url for S3
        s3 = connect_s3(self.config)
        return s3.generate_url(
            self.config['DOWNLOAD_LINK_EXPIRY'], 'GET', bucket=self.config['EBOOK_S3_BUCKET'], key=filename
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
                # select top-ranked version
                version = ebook['versions'][0]
            else:
                # iterate versions, break on first version which has the format we want
                for v in ebook['versions']:
                    for f in v['formats']:
                        if f['format'] == fmt and f['uploaded'] is True:
                            version = v
                            break
        else:
            version = next((v for v in ebook['versions'] if v['version_id'] == version_id), None)
            if version is None:
                raise NoFormatAvailableError('No version with id {}'.format(version_id))

        # iterate preferred_formats, break on first match on this version
        for fmt in preferred_formats:
            file_hash = next((
                f['file_hash'] for f in version['formats'] if f['format'] == fmt and f['uploaded'] is True
            ), None)
            if file_hash is not None:
                break

        # if no file_hash, we have a problem
        if file_hash is None:
            raise NoFormatAvailableError('Not found: {} {} {} {}'.format(ebook_id, version_id, fmt, user))

        return file_hash


    def increment_popularity(self, file_hash):
        """
        Increase an ebook version's popularity by one
        """
        # get the version_id from the file_hash
        version_id = r.table('formats').get(file_hash)['version_id'].run()

        # increment the popularity
        r.table('versions').get(version_id).update({
            'popularity': r.row['popularity']+1
        }).run()

        # reindex ebook version ranking
        self.set_version_rank(version_id)


    def set_version_rank(self, version_id):
        """
        Set a version's ranking, which is based on quality & popularity.
        See versions_rank_algorithm
        """
        # get the version object
        version = r.table('versions').get(version_id).run()
        # calculate ranking
        ranking = DataStore.versions_rank_algorithm(version['quality'], version['popularity'])
        # update the version table
        r.table('versions').get(version_id).update({'ranking': ranking}).run()


    def update_ebook_hash(self, current_file_hash, updated_file_hash):
        """
        Update a format with a new filehash (which is the primary key)
        This is called via the API after the OGRE-ID meta data is written into an ebook on the
        client, since changing the metadata changes the ebook's filehash
        """
        if current_file_hash == updated_file_hash:
            raise SameHashSuppliedOnUpdateError(current_file_hash)

        # check this filehash has already been processed
        exists = r.table('formats').get(updated_file_hash).run()
        if exists:
            return True

        data = r.table('formats').get(current_file_hash).run()
        if data is None:
            self.logger.error('Format {} does not exist'.format(current_file_hash))
            return False

        try:
            # update the ebook format as tagged by the client (insert/delete since changing PK)
            data['file_hash'] = updated_file_hash
            data['ogreid_tagged'] = True
            r.table('formats').insert(data).run()
            r.table('formats').get(current_file_hash).delete().run()
            self.logger.info('Updated {} to {} on {}'.format(
                current_file_hash, updated_file_hash, data['version_id'])
            )
        except Exception:
            self.logger.error(
                'Failed updating format {} on {}'.format(current_file_hash, data['version_id']),
                exc_info=True
            )
            return False

        return True

    def get_uploaded(self, file_hash):
        """
        Get all books marked as having been uploaded to S3
        """
        return r.table('formats').get(file_hash)['uploaded'].run()

    def set_uploaded(self, file_hash, username, filename, isit=True):
        """
        Mark an ebook as having been uploaded to S3
        """
        r.table('formats').get(file_hash).update({
            'uploaded': isit,
            'uploaded_by': username,
            's3_filename': filename,
        }).run()

    def set_dedrm_flag(self, file_hash):
        """
        Mark a book as having had DRM removed
        """
        r.table('formats').get(file_hash).update({'dedrm': True}).run()


    def store_ebook(self, ebook_id, file_hash, filepath, username):
        """
        Store an ebook on S3
        """
        s3 = connect_s3(self.config)
        bucket = s3.get_bucket(self.config['EBOOK_S3_BUCKET'])

        # generate a nice filename for this ebook
        filename = self._generate_filename(file_hash)

        self.logger.debug('Generated filename {} for {}'.format(filename, file_hash))

        # create a new storage key
        k = boto.s3.key.Key(bucket)
        k.key = filename

        # check if our file is already up on S3
        if k.exists() is True:
            metadata = k._get_remote_metadata()
            if 'x-amz-meta-ogre-key' in metadata and metadata['x-amz-meta-ogre-key'] == ebook_id:
                # if already exists, abort and flag as uploaded
                self.set_uploaded(file_hash, username, filename)
                return False

        try:
            # push file to S3
            k.set_contents_from_filename(
                filepath,
                headers={'x-amz-meta-ogre-key': ebook_id},
                md5=(file_hash,0)
            )
            self.logger.info('UPLOADED {}'.format(filename))

            # mark ebook as stored
            self.set_uploaded(file_hash, username, filename)

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
            # load the author and title of this book
            ebook_data = next(
                r.table('formats').filter({'file_hash': file_hash}).eq_join(
                    'version_id', r.table('versions'), index='version_id'
                ).zip().eq_join(
                    'ebook_id', r.table('ebooks'), index='ebook_id'
                ).zip().pluck(
                    'author', 'title', 'format'
                ).run(), None
            )
            author = ebook_data['author']
            title = ebook_data['title']
            fmt = ebook_data['format']

        elif fmt is None:
            # load the file format for this book's hash
            fmt = r.table('formats').get(file_hash).pluck('format').run()['format']

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


    def get_missing_books(self, username=None):
        """
        Query the DB for books marked as not uploaded
        """
        # query the formats table for missing ebooks
        query = r.table('formats').get_all(False, index='uploaded')

        # join up to the versions table
        query = query.eq_join('version_id', r.table('versions'), index='version_id').zip()

        # filter by username
        if username is not None:
            query = query.filter(lambda d: d['owners'].contains(username))

        # return a list of file_hashes
        cursor = query['file_hash'].run()

        # flatten for output
        return list(cursor)


    def log_event(self, user, syncd_books_count, new_books_count):
        """
        Add entries to a log every time a user syncs from ogreclient
        """
        return r.table('sync_events').insert({
            'username': user.username,
            'syncd_books_count': syncd_books_count,
            'new_books_count': new_books_count,
            'timestamp': r.now(),
        }).run()
