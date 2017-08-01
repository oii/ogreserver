from __future__ import absolute_import
from __future__ import unicode_literals

import ftfy

from flask import current_app as app

from .stores import ebooks as ebook_store
from .utils.ebooks import generate_ebook_id

from . import exceptions


def update_library(ebooks, user):
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
            author, title = _parse_and_sanitize(
                authortitle, incoming['meta'], file_hash=incoming['file_hash'][0:7]
            )

            existing_ebook = None

            try:
                # check for ogre_id from metadata passed as ebook_id
                existing_ebook = ebook_store.load_ebook(incoming['ebook_id'])

                # remove ebook_id from incoming metadata dict
                del(incoming['ebook_id'])

            except KeyError as e:
                # verify if this ebook_id already exists in the DB, but is not on the incoming ebook
                existing_ebook = ebook_store.load_ebook(generate_ebook_id(author, title))

                # tell client to set ogre_id on this ebook
                output[incoming['file_hash']]['update'] = True

            # check if this exact file has been uploaded before
            identical_ebook = ebook_store.load_ebook_by_file_hash(incoming['file_hash'])
            if identical_ebook:
                raise exceptions.FileHashDuplicateError(identical_ebook.id, incoming['file_hash'])

            else:
                # check if original source ebook was uploaded with this hash
                original_ebook = ebook_store.load_ebook_by_original_file_hash(incoming['file_hash'])

                if original_ebook is not None:
                    raise exceptions.FileHashDuplicateError(
                        original_ebook.id,
                        original_ebook.versions[0].source_format.file_hash
                    )

            if not existing_ebook:
                # check for ASIN & ISBN duplicates
                # the assumption is that ASIN dupes are the same book from the Amazon store
                if 'asin' in incoming['meta']:
                    existing_ebook = ebook_store.load_ebook_by_asin(incoming['meta']['asin'])
                    if existing_ebook:
                        raise exceptions.AsinDuplicateError(existing_ebook.id)

                if 'isbn' in incoming['meta']:
                    existing_ebook = ebook_store.load_ebook_by_isbn(incoming['meta']['isbn'])
                    if existing_ebook:
                        raise exceptions.IsbnDuplicateError(existing_ebook.id)

                # check for author/title duplicates
                existing_ebook = ebook_store.load_ebook_by_authortitle(author, title)

                if existing_ebook:
                    # duplicate authortitle found
                    # must be a new version of the book else it would have been matched above
                    # don't accept new version of book from user who has already syncd it before
                    if existing_ebook.original_version.uploader is user:
                        raise exceptions.AuthortitleDuplicateError(existing_ebook.id, incoming['file_hash'])

                else:
                    # new books are easy
                    ebook = ebook_store.create_ebook(title, author, user, incoming)

                    # mark book as new
                    output[incoming['file_hash']]['ebook_id'] = ebook.id
                    output[incoming['file_hash']]['new'] = True
                    continue

            # create new version, with its initial format
            ebook_store.create_version(
                existing_ebook,
                user,
                incoming['file_hash'],
                incoming['format'],
                incoming['size'],
                incoming['dedrm'],
            )

            # mark with ebook_id and continue
            output[incoming['file_hash']]['ebook_id'] = existing_ebook.id


        except exceptions.DuplicateBaseError as e:
            if e.file_hash:
                # increase popularity of existing duplicate ebook
                ebook_store.increment_popularity(e.file_hash)

                # add the current user as an owner of this file
                ebook_store.append_owner(e.file_hash, user)

            # enable client to update book with ebook_id
            output[incoming['file_hash']]['ebook_id'] = e.ebook_id

            # inform client of duplicate
            output[incoming['file_hash']]['dupe'] = True

        except exceptions.OgreException as e:
            # log this and report back to client
            app.logger.info(e)
            output[incoming['file_hash']]['error'] = unicode(e).encode('utf8')

            # don't update on client for failed books
            output[incoming['file_hash']]['update'] = False

        except Exception as e:
            app.logger.error(e, exc_info=True)

            # don't update on client for failed books
            output[incoming['file_hash']]['update'] = False

    return output


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
        raise exceptions.BadMetaDataError("Bad meta data on {}: {}".format(
            file_hash,
            authortitle.replace('\u0007', ' ').replace('\u0006', ' ')
        ), e)

    # recombine firstname, lastname into author
    author = '{} {}'.format(firstname, lastname)
    return author, title
