from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import division

import json
import os

import urllib
import urllib2
from urllib2 import HTTPError, URLError
from .urllib2_file import newHTTPHandler

from .ebook_obj import EbookObject
from .utils import make_temp_directory
from .printer import CliPrinter
from .dedrm import decrypt, DRM, DeDrmMissingError, DecryptionFailed

from .definitions import EBOOK_FORMATS

from .exceptions import AuthDeniedError, AuthError, NoEbooksError
from .exceptions import DuplicateEbookBaseError, ExactDuplicateEbookError, AuthortitleDuplicateEbookError
from .exceptions import SyncError, UploadError, CorruptEbookError
from .exceptions import FailedWritingMetaDataError, FailedConfirmError, FailedDebugLogsError
from .exceptions import MissingFromCacheError, OgreException, OgreserverDownError


def authenticate(host, username, password):
    try:
        # authenticate the user; retrieve an session_key for subsequent requests
        req = urllib2.Request(
            url='http://{}/login'.format(host),
            data=json.dumps({
                'email': username,
                'password': password
            }),
            headers={
                'Content-type': 'application/json'
            }
        )
        f = urllib2.urlopen(req)
        data = json.loads(f.read())

        if data['meta']['code'] == 200:
            return data['response']['user']['authentication_token']
        else:
            raise AuthError(json.dumps(data))

    except KeyError as e:
        raise AuthError(inner_excp=e)
    except HTTPError as e:
        if e.getcode() == 403:
            raise AuthDeniedError
        else:
            raise AuthError(inner_excp=e)
    except URLError as e:
        if 'Connection refused' in str(e):
            raise OgreserverDownError
        else:
            raise AuthError(inner_excp=e)


def sync(config, prntr):
    # authenticate user and generate session API key
    session_key = authenticate(config['host'], config['username'], config['password'])

    # 1) find ebooks in config['ebook_home'] on local machine
    ebooks_dict, errord_list = search_for_ebooks(config, prntr)

    if len(errord_list) > 0:
        prntr.p('Errors occurred during scan:')
        for message, e in errord_list.iteritems():
            prntr.e('{}'.format(unicode(message)), excp=e)

    # 2) remove DRM
    if config['no_drm'] is False:
        errord_list = clean_all_drm(config, prntr, ebooks_dict)

        if len(errord_list) > 0:
            prntr.p('Errors occurred during decryption:')
            for message, e in errord_list.iteritems():
                prntr.e('{}'.format(unicode(message)), excp=e)

    # 3) send dict of ebooks / md5s to ogreserver
    response = sync_with_server(config, prntr, session_key, ebooks_dict)

    if not response['ebooks_to_upload'] and not response['ebooks_to_update']:
        # filter the OgreWarnings out of the error list
        errord_list = [err for err in errord_list if isinstance(err, OgreException)]

        if not errord_list:
            prntr.p('Finished, nothing to do.')
        else:
            if config['debug'] is False:
                prntr.e('Finished with errors. Re-run with --debug to send logs to OGRE')
            else:
                prntr.e('Finished with errors.')
                send_logs(prntr, config['host'], session_key, errord_list)
        return

    prntr.p('Come on sucker, lick my battery')

    # 4) set ogre_id in metadata of each sync'd ebook
    update_local_metadata(
        config, prntr, session_key, ebooks_dict, response['ebooks_to_update']
    )

    # 5) upload the ebooks requested by ogreserver
    upload_ebooks(
        config, prntr, session_key, ebooks_dict, response['ebooks_to_upload']
    )

    # 6) send a log of all events, and upload bad books
    if config['debug'] is True:
        send_logs(prntr, config['host'], session_key, errord_list)


def stats(config, prntr, ebooks_dict=None):
    ebooks_dict, errord_list = search_for_ebooks(config, prntr)

    counts = {}
    errors = {}

    # iterate authortitle:EbookObject pairs
    for key, e in ebooks_dict.iteritems():
        if e.format not in counts.keys():
            counts[e.format] = 1
        else:
            counts[e.format] += 1

    # iterate list of exceptions
    for e in errord_list.values():
        if isinstance(e, CorruptEbookError):
            if 'corrupt' not in errors.keys():
                errors['corrupt'] = 1
            else:
                errors['corrupt'] += 1
        elif isinstance(e, DuplicateEbookBaseError):
            if 'duplicate' not in errors.keys():
                errors['duplicate'] = 1
            else:
                errors['duplicate'] += 1

    # add header to output table
    output = [('format', 'count')]
    output += [(k,v) for k,v in counts.iteritems()]
    # add a separator row and the error counts
    output.append(('-', '-'))
    output += [(k,v) for k,v in errors.iteritems()]

    # print table
    prntr.p(output, CliPrinter.STATS, tabular=True, notime=True)


def search_for_ebooks(config, prntr):
    ebooks = []

    # let the user know something is happening
    prntr.p('Searching for ebooks.. ', nonl=True)

    # process ebooks in a directory
    def _process_ebook_dir(root, files):
        for filename in files:
            fn, ext = os.path.splitext(filename)
            # check file not hidden, is in list of known file suffixes
            if fn[1:1] != '.' and ext[1:] in EBOOK_FORMATS.keys():
                ebooks.append(
                    (os.path.join(root, filename), ext[1:])
                )

    # search for ebooks in all provider dirs & ebook_home
    for provider_dir in config['providers'].values() + [config['ebook_home']]:
        if config['debug']:
            prntr.p('Searching {}'.format(provider_dir))

        for root, _, files in os.walk(provider_dir):
            _process_ebook_dir(root, files)

    i = 0
    prntr.p('Discovered {} files'.format(len(ebooks)))
    if len(ebooks) == 0:
        raise NoEbooksError

    prntr.p('Scanning ebook meta data and checking DRM..')
    ebooks_by_authortitle = {}
    ebooks_by_filehash = {}
    errord_list = {}

    for item in ebooks:
        try:
            # skip the cache during debug
            if config['debug'] is True and config['use_cache'] is False:
                raise MissingFromCacheError

            # get ebook from the cache
            ebook_obj = config['ebook_cache'].get_ebook(path=item[0])

        except MissingFromCacheError:
            # init the EbookObject
            ebook_obj = EbookObject(
                config=config,
                filepath=item[0],
                fmt=item[1],
            )
            # calculate MD5 of ebook
            ebook_obj.compute_md5()

            try:
                # extract ebook metadata and build key; books are stored in a dict
                # with 'authortitle' as the key in a naive attempt at de-deduplication
                ebook_obj.get_metadata()

            except CorruptEbookError as e:
                # record books which failed during search
                errord_list[ebook_obj.path] = e

                # add book to the cache as a skip
                ebook_obj.skip = True
                config['ebook_cache'].store_ebook(ebook_obj)

                # skip books which can't have metadata extracted
                continue

        # check for identical filehash (exact duplicate) or duplicated authortitle/format
        if ebook_obj.file_hash in ebooks_by_filehash.keys():
            # warn user on error stack
            errord_list[ebook_obj.path] = ExactDuplicateEbookError(
                ebook_obj, ebooks_by_authortitle[ebook_obj.authortitle].path
            )
        elif ebook_obj.authortitle in ebooks_by_authortitle.keys() and ebooks_by_authortitle[ebook_obj.authortitle].format == ebook_obj.format:
            # warn user on error stack
            errord_list[ebook_obj.path] = AuthortitleDuplicateEbookError(
                ebook_obj, ebooks_by_authortitle[ebook_obj.authortitle].path
            )
        else:
            # new ebook, or different format of duplicate ebook found
            write = False

            if ebook_obj.authortitle in ebooks_by_authortitle.keys():
                # compare the rank of the format already found against this one
                existing_rank = EBOOK_FORMATS.keys().index(ebooks_by_authortitle[ebook_obj.authortitle].format)
                new_rank = EBOOK_FORMATS.keys().index(ebook_obj.format)

                # lower is better
                if new_rank < existing_rank:
                    write = True
            else:
                # new book found
                write = True

            if write:
                # output dictionary for sending to ogreserver
                ebooks_by_authortitle[ebook_obj.authortitle] = ebook_obj

                # track all unique file hashes found
                ebooks_by_filehash[ebook_obj.file_hash] = ebook_obj
            else:
                ebook_obj.skip = True

        # add book to the cache
        config['ebook_cache'].store_ebook(ebook_obj)

        i += 1
        prntr.progressf(num_blocks=i, total_size=len(ebooks))

    prntr.p('Found {} ebooks'.format(len(ebooks_by_authortitle)), success=True)

    if len(ebooks_by_authortitle) == 0:
        return {}, errord_list

    return ebooks_by_authortitle, errord_list


def clean_all_drm(config, prntr, ebooks_dict):
    errord_list = {}

    i = 0
    cleaned = 0

    for authortitle, ebook_obj in ebooks_dict.iteritems():
        # only attempt decrypt on ebooks which are defined as is_valid_format
        if EBOOK_FORMATS[ebook_obj.format][0] is False:
            continue

        try:
            filename, suffix = os.path.splitext(os.path.basename(ebook_obj.path))

            # remove DRM from ebook
            new_ebook_obj = remove_drm_from_ebook(
                config, prntr, ebook_obj.path, ebook_obj.file_hash, suffix
            )

            if new_ebook_obj is not None:
                # update the sync data with the decrypted ebook
                ebooks_dict[authortitle] = new_ebook_obj
                cleaned += 1

        except CorruptEbookError as e:
            # record books which failed due to unicode filename issues
            errord_list[ebook_obj.path] = e
            continue

        if config['verbose'] is False:
            i += 1
            prntr.progressf(num_blocks=i, total_size=len(ebooks_dict))

    if config['verbose'] is False:
        prntr.p('Cleaned DRM from {} ebooks'.format(cleaned), success=True)

    return errord_list


def remove_drm_from_ebook(config, prntr, filepath, file_hash, suffix):
    if config['debug'] is False or config['use_cache'] is True:
        try:
            # attempt load ebook from local cache
            ebook_obj = config['ebook_cache'].get_ebook(filepath, file_hash)

            # return if book marked DRM free in the cache
            if ebook_obj.drmfree is True or ebook_obj.skip is True:
                return None

        except MissingFromCacheError:
            pass

    ebook_obj = None

    try:
        # decrypt into a temp path
        with make_temp_directory() as ebook_output_path:
            state, decrypted_filepath = decrypt(
                filepath, suffix, config['config_dir'], output_dir=ebook_output_path
            )

            if state == DRM.none:
                # update cache to mark book as drmfree
                config['ebook_cache'].update_ebook_property(filepath, drmfree=True)

            elif state == DRM.decrypted:
                if config['verbose']:
                    prntr.p('DRM removed from {}'.format(filepath), CliPrinter.DEDRM, success=True)

                # create new ebook_obj for decrypted ebook
                ebook_obj = EbookObject(config=config, filepath=decrypted_filepath)
                ebook_obj.compute_md5()

                # add the OGRE DeDRM tag to the decrypted ebook
                # TODO handle CorruptEbookError via get_metadata
                ebook_obj.add_dedrm_tag()

                # init OGRE directory in user's ebook dir
                if not os.path.exists(os.path.join(config['ebook_home'], 'ogre')):
                    os.mkdir(os.path.join(config['ebook_home'], 'ogre'))

                # move decrypted book into ebook library
                ebook_obj.path = os.path.join(
                    config['ebook_home'], 'ogre', os.path.basename(decrypted_filepath)
                )
                os.rename(decrypted_filepath, ebook_obj.path)

                if config['verbose']:
                    prntr.p('Decrypted book moved to {}'.format(ebook_obj.path), CliPrinter.DEDRM, success=True)

                # mark decrypted book as drmfree=True in cache
                config['ebook_cache'].update_ebook_property(filepath, ebook_obj.file_hash, drmfree=True)

                # update existing DRM-scuppered as skip=True in cache
                config['ebook_cache'].update_ebook_property(filepath, skip=True)

            else:
                # mark book as having DRM
                config['ebook_cache'].update_ebook_property(filepath, drmfree=False)

                if state == DRM.wrong_key:
                    raise DecryptionFailed('Incorrect key found for ebook')
                elif state == DRM.corrupt:
                    raise DecryptionFailed('Corrupt ebook found')
                else:
                    raise DecryptionFailed('Unknown error in decryption ({})'.format(state))

    except DeDrmMissingError:
        config['no_drm'] = True
    except (DecryptionFailed, UnicodeDecodeError) as e:
        raise CorruptEbookError(filepath, inner_excp=e)

    return ebook_obj


def sync_with_server(config, prntr, session_key, ebooks_dict):
    # serialize ebooks to dictionary for sending to ogreserver
    ebooks_for_sync = {}
    for authortitle, ebook_obj in ebooks_dict.iteritems():
        # only send format is defined as is_valid_format
        if EBOOK_FORMATS[ebook_obj.format][0] is True:
            ebooks_for_sync[authortitle] = ebook_obj.serialize()

    try:
        # post json dict of ebook data
        req = urllib2.Request(
            url='http://{}/api/v1/post'.format(
                config['host']
            ),
            data=json.dumps(ebooks_for_sync),
            headers={
                'Content-type': 'application/json',
                'Ogre-key': session_key
            },
        )
        resp = urllib2.urlopen(req)
        data = resp.read()

        response = json.loads(data)

    except (HTTPError, URLError) as e:
        raise SyncError(inner_excp=e)

    # display server messages
    for msg in response['messages']:
        if len(msg) == 2:
            prntr.p('{} {}'.format(msg[0], msg[1]), CliPrinter.RESPONSE)
        else:
            prntr.p(msg, CliPrinter.RESPONSE)

    for msg in response['errors']:
        prntr.e(msg, CliPrinter.RESPONSE)

    return response


def update_local_metadata(config, prntr, session_key, ebooks_dict, ebooks_to_update):
    success, failed = 0, 0

    # update any books with ogre_id supplied from ogreserver
    for file_hash, item in ebooks_to_update.iteritems():
        # find this book in the scan data
        for authortitle, ebook_obj in ebooks_dict.iteritems():
            if file_hash == ebook_obj.file_hash:
                try:
                    # update the metadata on the ebook, and communicate that to ogreserver
                    new_file_hash = ebook_obj.add_ogre_id_tag(item['ebook_id'], session_key)

                    success += 1
                    if config['verbose']:
                        prntr.p('Wrote OGRE_ID to {}'.format(ebook_obj.path))

                    # write to ogreclient cache
                    config['ebook_cache'].update_ebook_property(ebook_obj.path, file_hash=new_file_hash)

                except (FailedWritingMetaDataError, FailedConfirmError) as e:
                    prntr.e('Failed saving OGRE_ID in {}'.format(ebook_obj.path), excp=e)
                    failed += 1

    if success > 0:
        prntr.p('Updated {} ebooks'.format(success), success=True)
    if failed > 0:
        prntr.e('Failed updating {} ebooks'.format(failed))


def upload_ebooks(config, prntr, session_key, ebooks_dict, ebooks_to_upload):
    if len(ebooks_to_upload) == 0:
        return

    # grammatically correct messages are nice
    plural = 's' if len(ebooks_to_upload) > 1 else ''

    prntr.p('Uploading {} file{}. Go make a brew.'.format(len(ebooks_to_upload), plural))

    success, failed, i = 0, 0, 0

    # upload each requested by the server
    for upload in ebooks_to_upload:
        # iterate all user's found books
        for authortitle, ebook_obj in ebooks_dict.iteritems():
            if upload['file_hash'] == ebook_obj.file_hash:
                try:
                    upload_single_book(config['host'], session_key, ebook_obj.path, upload)
                    success += 1

                except UploadError as e:
                    prntr.e('Failed uploading {}'.format(ebook_obj.path), excp=e)
                    failed += 1

        i += 1
        prntr.progressf(num_blocks=i, total_size=len(ebooks_to_upload))

    if success > 0:
        prntr.p('Completed {} uploads'.format(success), success=True)
    if failed > 0:
        prntr.e('Failed uploading {} ebooks'.format(failed))


def upload_single_book(host, session_key, filepath, upload_obj):
    try:
        with open(filepath, "rb") as f:
            # configure for uploads
            opener = urllib2.build_opener(newHTTPHandler())
            opener.addheaders = [
                ('Ogre-key', session_key)
            ]

            # build the post params
            params = {
                'ebook_id': upload_obj['ebook_id'],
                'file_hash': upload_obj['file_hash'],
                'format': upload_obj['format'],
                'ebook': f,
            }
            req = opener.open(
                'http://{}/api/v1/upload'.format(host), params
            )
            return req.read()

    except (HTTPError, URLError), e:
        raise UploadError(inner_excp=e)
    except IOError, e:
        pass


def send_logs(prntr, host, session_key, errord_list):
    try:
        log_data = '\n'.join(prntr.logs).encode('utf-8')

        # post all logs to ogreserver
        req = urllib2.Request(
            url='http://{}/api/v1/post-logs'.format(host),
            data=log_data,
            headers={
                'Content-type': 'application/json',
                'Ogre-key': session_key
            },
        )
        resp = urllib2.urlopen(req)
        data = resp.read()

        if data != 'ok':
            raise FailedDebugLogsError('Failed storing the logs, please report this.')
        else:
            prntr.p('Uploaded logs to OGRE')

        # upload all books which failed
        if errord_list:
            prntr.p('Uploaded failed books to OGRE for debug..')

            opener = urllib2.build_opener(newHTTPHandler())
            opener.addheaders = [
                ('Ogre-key', session_key)
            ]

            i = 0

            for filepath in errord_list.keys():
                filename = os.path.basename(filepath.encode('utf-8'))

                with open(filepath, "rb") as f:
                    # post the file contents
                    req = opener.open(
                        'http://{}/api/v1/upload-errord/{}'.format(
                            host,
                            urllib.quote_plus(filename),
                        ),
                        {'ebook': f},
                    )
                    # ignore failures here
                    req.read()

                i += 1
                prntr.progressf(num_blocks=i, total_size=len(errord_list))

    except (HTTPError, URLError) as e:
        raise FailedDebugLogsError(inner_excp=e)
