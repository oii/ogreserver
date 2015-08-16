from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import division

import json
import os
import shutil

import urllib
import urllib2
from urllib2 import HTTPError, URLError
from .urllib2_file import newHTTPHandler

from .ebook_obj import EbookObject
from .utils import make_temp_directory, retry
from .printer import CliPrinter
from .providers import LibProvider, PathsProvider
from .dedrm import decrypt, DRM

from .exceptions import AuthDeniedError, AuthError, NoEbooksError, DuplicateEbookBaseError, \
        ExactDuplicateEbookError, AuthortitleDuplicateEbookError, EbookIdDuplicateEbookError, \
        SyncError, UploadError, CorruptEbookError, FailedWritingMetaDataError, \
        FailedConfirmError, FailedDebugLogsError, MissingFromCacheError, OgreException, \
        OgreserverDownError, FailedUploadsQueryError, FailedGettingDefinitionsError, \
        DeDrmMissingError, DecryptionFailed


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


def get_definitions(config, session_key):
    try:
        # retrieve the ebook format definitions
        req = urllib2.Request(
            url='http://{}/api/v1/definitions'.format(config['host']),
            headers={
                'Ogre-key': session_key
            },
        )
        f = urllib2.urlopen(req)
        return json.loads(f.read())

    except Exception as e:
        raise FailedGettingDefinitionsError(inner_excp=e)


def sync(config, prntr):
    # authenticate user and generate session API key
    session_key = authenticate(config['host'], config['username'], config['password'])

    # query the server for current ebook definitions (which file extensions to search for etc)
    config['definitions'] = get_definitions(config, session_key)

    # let the user know something is happening
    prntr.p('Searching for ebooks..', nonl=True)

    # 1) find ebooks in config['ebook_home'] on local machine
    ebooks_by_authortitle, ebooks_by_filehash, errord_list = search_for_ebooks(config, prntr)

    if len(errord_list) > 0:
        prntr.p('Errors occurred during scan:')
        for e in errord_list:
            prntr.e(e.ebook_obj.path, excp=e)

    # 2) remove DRM
    errord_list = clean_all_drm(config, prntr, ebooks_by_authortitle, ebooks_by_filehash)

    if len(errord_list) > 0:
        prntr.p('Errors occurred during decryption:')
        for e in errord_list:
            # display an error message
            prntr.e(e.ebook_obj.path, excp=e)
            # remove the book from the sync data
            del(ebooks_by_filehash[e.ebook_obj.file_hash])
            del(ebooks_by_authortitle[e.ebook_obj.authortitle])

    prntr.p('Found {} ebooks'.format(len(ebooks_by_authortitle)), success=True)

    # 3) send dict of ebooks / md5s to ogreserver
    response = sync_with_server(config, prntr, session_key, ebooks_by_authortitle)

    prntr.p('Come on sucker, lick my battery')

    # 4) set ogre_id in metadata of each sync'd ebook
    update_local_metadata(config, prntr, session_key, ebooks_by_filehash, response['to_update'])

    # 5) query the set of books to upload
    ebooks_to_upload = query_for_uploads(config, prntr, session_key)

    # 6) upload the ebooks requested by ogreserver
    upload_ebooks(config, prntr, session_key, ebooks_by_filehash, ebooks_to_upload)

    # 7) display/send errors
    errord_list = [err for err in errord_list if isinstance(err, OgreException)]

    if errord_list:
        if not config['debug']:
            prntr.e('Finished with errors. Re-run with --debug to send logs to OGRE')
        else:
            # send a log of all events, and upload bad books
            send_logs(prntr, config['host'], session_key, errord_list)
    else:
        prntr.p('Finished, nothing further to do.')


def stats(config, prntr, ebooks_by_authortitle=None):
    ebooks_by_authortitle, ebooks_by_filehash, errord_list = search_for_ebooks(config, prntr)

    counts = {}
    errors = {}

    # iterate authortitle:EbookObject pairs
    for key, e in ebooks_by_authortitle.iteritems():
        if e.format not in counts.keys():
            counts[e.format] = 1
        else:
            counts[e.format] += 1

    # iterate list of exceptions
    for e in errord_list:
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

    # process ebooks in a directory
    def _process_ebook_dir(root, files):
        for filename in files:
            fn, ext = os.path.splitext(filename)
            # check file not hidden, is in list of known file suffixes
            if fn[1:1] != '.' and ext[1:] in config['definitions'].keys():
                ebooks.append(
                    (os.path.join(root, filename), ext[1:])
                )

    # LibProviders have paths to other locations where books are stored
    provider_dirs = [
        provider.libpath for provider in config['providers'].values()
        if type(provider) is LibProvider
    ]

    # search for ebooks in all provider dirs & ebook_home
    for provider_dir in provider_dirs + [config['ebook_home']]:
        if config['debug']:
            prntr.p('Searching {}'.format(provider_dir))

        for root, _, files in os.walk(provider_dir):
            _process_ebook_dir(root, files)

    # PathsProviders have list of ebook paths already loaded: merge those now
    provider_ebooks = [
        provider.paths for provider in config['providers'].values()
        if type(provider) is PathsProvider
    ]
    for l in provider_ebooks:
        ebooks += l

    i = 0
    prntr.p('Discovered {} files'.format(len(ebooks)))
    if len(ebooks) == 0:
        raise NoEbooksError

    prntr.p('Scanning ebook meta data and checking DRM..')
    ebooks_by_authortitle = {}
    ebooks_by_filehash = {}
    errord_list = []

    for item in ebooks:
        try:
            # optionally skip the cache
            if config['skip_cache'] is True:
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
                errord_list.append(e)

                # add book to the cache as a skip
                ebook_obj.skip = True
                config['ebook_cache'].store_ebook(ebook_obj)

        # skip previously scanned books which are marked skip (DRM'd or duplicates)
        if ebook_obj.skip:
            i += 1
            prntr.progressf(num_blocks=i, total_size=len(ebooks))
            continue

        # check for identical filehash (exact duplicate) or duplicated authortitle/format
        if ebook_obj.file_hash in ebooks_by_filehash.keys():
            # warn user on error stack
            errord_list.append(
                ExactDuplicateEbookError(ebook_obj, ebooks_by_authortitle[ebook_obj.authortitle].path)
            )
        elif ebook_obj.authortitle in ebooks_by_authortitle.keys() and ebooks_by_authortitle[ebook_obj.authortitle].format == ebook_obj.format:
            # warn user on error stack
            errord_list.append(
                AuthortitleDuplicateEbookError(ebook_obj, ebooks_by_authortitle[ebook_obj.authortitle].path)
            )
        else:
            # new ebook, or different format of duplicate ebook found
            write = False

            if ebook_obj.authortitle in ebooks_by_authortitle.keys():
                # compare the rank of the format already found against this one
                existing_rank = config['definitions'].keys().index(ebooks_by_authortitle[ebook_obj.authortitle].format)
                new_rank = config['definitions'].keys().index(ebook_obj.format)

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

        try:
            # add book to the cache
            config['ebook_cache'].store_ebook(ebook_obj)

        except EbookIdDuplicateEbookError as e:
            # handle duplicate books with same ebook_id in metadata
            errord_list.append(e)

        i += 1
        prntr.progressf(num_blocks=i, total_size=len(ebooks))

    if len(ebooks_by_authortitle) == 0:
        return {}, {}, errord_list

    return ebooks_by_authortitle, ebooks_by_filehash, errord_list


def clean_all_drm(config, prntr, ebooks_by_authortitle, ebooks_by_filehash):
    errord_list = []

    i = 0
    cleaned = 0

    for authortitle, ebook_obj in ebooks_by_authortitle.iteritems():
        # skip if book already DRM free or marked skip
        if ebook_obj.drmfree is True or ebook_obj.skip is True:
            continue

        # only attempt decrypt on ebooks which are defined as is_valid_format
        if config['definitions'][ebook_obj.format][0] is False:
            continue

        try:
            # remove DRM from ebook
            new_ebook_obj = remove_drm_from_ebook(config, prntr, ebook_obj)

            if new_ebook_obj is not None:
                # update the sync data with the decrypted ebook
                ebooks_by_authortitle[authortitle] = new_ebook_obj
                del(ebooks_by_filehash[ebook_obj.file_hash])
                ebooks_by_filehash[new_ebook_obj.file_hash] = new_ebook_obj
                cleaned += 1

        # record books which failed decryption
        except DeDrmMissingError as e:
            errord_list.append(DeDrmMissingError(ebook_obj))
            continue
        except (CorruptEbookError, DecryptionFailed) as e:
            errord_list.append(e)
            continue

        if config['verbose'] is False:
            i += 1
            prntr.progressf(num_blocks=i, total_size=len(ebooks_by_authortitle))

    if config['verbose'] is False:
        prntr.p('Cleaned DRM from {} ebooks'.format(cleaned), success=True)

    return errord_list


def remove_drm_from_ebook(config, prntr, ebook_obj):
    decrypted_ebook_obj = None

    # extract suffix
    _, suffix = os.path.splitext(os.path.basename(ebook_obj.path))

    try:
        # decrypt into a temp path
        with make_temp_directory() as ebook_output_path:
            state, decrypted_filepath = decrypt(
                ebook_obj.path, suffix, config['config_dir'], output_dir=ebook_output_path
            )

            if state == DRM.none:
                # update cache to mark book as drmfree
                config['ebook_cache'].update_ebook_property(ebook_obj.path, drmfree=True)

            elif state == DRM.decrypted:
                if config['verbose']:
                    prntr.p('DRM removed from {}'.format(ebook_obj.path), CliPrinter.DEDRM, success=True)

                # create new ebook_obj for decrypted ebook
                decrypted_ebook_obj = EbookObject(config=config, filepath=decrypted_filepath)
                decrypted_ebook_obj.compute_md5()

                # add the OGRE DeDRM tag to the decrypted ebook
                # TODO handle CorruptEbookError via get_metadata
                decrypted_ebook_obj.add_dedrm_tag()

                # init OGRE directory in user's ebook dir
                if not os.path.exists(os.path.join(config['ebook_home'], 'ogre')):
                    os.mkdir(os.path.join(config['ebook_home'], 'ogre'))

                # move decrypted book into ebook library
                decrypted_ebook_obj.path = os.path.join(
                    config['ebook_home'], 'ogre', os.path.basename(decrypted_filepath)
                )
                shutil.move(decrypted_filepath, decrypted_ebook_obj.path)

                if config['verbose']:
                    prntr.p('Decrypted book moved to {}'.format(decrypted_ebook_obj.path), CliPrinter.DEDRM, success=True)

                # add decrypted book to cache
                config['ebook_cache'].store_ebook(decrypted_ebook_obj)

                # update existing DRM-scuppered book as skip=True in cache
                config['ebook_cache'].update_ebook_property(ebook_obj.path, skip=True)

            else:
                # mark book as having DRM
                config['ebook_cache'].update_ebook_property(ebook_obj.path, drmfree=False)

                if state == DRM.wrong_key:
                    raise DecryptionFailed(ebook_obj, 'Incorrect key found for ebook')
                elif state == DRM.corrupt:
                    raise DecryptionFailed(ebook_obj, 'Corrupt ebook found')
                else:
                    raise DecryptionFailed(ebook_obj, 'Unknown error in decryption ({})'.format(state))

    except UnicodeDecodeError as e:
        raise CorruptEbookError(ebook_obj, 'Unicode filename problem', inner_excp=e)

    return decrypted_ebook_obj


def sync_with_server(config, prntr, session_key, ebooks_by_authortitle):
    # serialize ebooks to dictionary for sending to ogreserver
    ebooks_for_sync = {}
    for authortitle, ebook_obj in ebooks_by_authortitle.iteritems():
        # only send format is defined as is_valid_format
        if config['definitions'][ebook_obj.format][0] is True:
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


def update_local_metadata(config, prntr, session_key, ebooks_by_filehash, ebooks_to_update):
    success, failed = 0, 0

    # update any books with ogre_id supplied from ogreserver
    for file_hash, item in ebooks_to_update.iteritems():
        ebook_obj = ebooks_by_filehash[file_hash]

        try:
            # update the metadata on the ebook, and communicate that to ogreserver
            new_file_hash = ebook_obj.add_ogre_id_tag(item['ebook_id'], session_key)

            # update the global dict with the new file_hash
            del(ebooks_by_filehash[file_hash])
            ebooks_by_filehash[new_file_hash] = ebook_obj

            success += 1
            if config['verbose']:
                prntr.p('Wrote OGRE_ID to {}'.format(ebook_obj.path))

            # write to ogreclient cache
            config['ebook_cache'].update_ebook_property(
                ebook_obj.path,
                file_hash=new_file_hash,
                ebook_id=item['ebook_id']
            )

        except (FailedWritingMetaDataError, FailedConfirmError) as e:
            prntr.e('Failed saving OGRE_ID in {}'.format(ebook_obj.path), excp=e)
            failed += 1

    if success > 0:
        prntr.p('Updated {} ebooks'.format(success), success=True)
    if failed > 0:
        prntr.e('Failed updating {} ebooks'.format(failed))


def query_for_uploads(config, prntr, session_key):
    try:
        # query ogreserver for books to upload
        req = urllib2.Request(
            url='http://{}/api/v1/to-upload'.format(config['host']),
            headers={
                'Content-type': 'application/json',
                'Ogre-key': session_key
            },
        )
        resp = urllib2.urlopen(req)
        return json.loads(resp.read())

    except (HTTPError, URLError) as e:
        raise FailedUploadsQueryError(inner_excp=e)


def upload_ebooks(config, prntr, session_key, ebooks_by_filehash, ebooks_to_upload):
    if len(ebooks_to_upload) == 0:
        return

    # grammatically correct messages are nice
    plural = 's' if len(ebooks_to_upload) > 1 else ''

    prntr.p('Uploading {} file{}. Go make a brew.'.format(len(ebooks_to_upload), plural))

    success, i = 0, 0
    failed_uploads = []

    # upload each requested by the server
    for file_hash in ebooks_to_upload:
        ebook_obj = ebooks_by_filehash[file_hash]

        # failed uploads are retried three times;
        # a total fail will raise the last exception
        try:
            upload_single_book(config['host'], session_key, ebook_obj)

        except UploadError as e:
            # print failures or save for later
            if config['verbose'] is True:
                prntr.e('Failed uploading {}'.format(ebook_obj.path), excp=e)
            else:
                failed_uploads.append(e)
        else:
            if config['verbose'] is True:
                prntr.p('Uploaded {}'.format(ebook_obj.path), success=True)
            success += 1

        if config['verbose'] is False:
            i += 1
            prntr.progressf(num_blocks=i, total_size=len(ebooks_to_upload))

    # only print completion message after all retries
    if success > 0:
        prntr.p('Completed {} uploads'.format(success), success=True)

    if len(failed_uploads) > 0:
        prntr.e('Failed uploading {} ebooks:'.format(len(failed_uploads)))
        for e in failed_uploads:
            prntr.e(
                '{}'.format(
                    ebooks_by_filehash[e.ebook_obj.file_hash].path
                ), excp=e.inner_excp
            )
        prntr.p('Please run another sync', success=True)


@retry(times=3)
def upload_single_book(host, session_key, ebook_obj):
    try:
        with open(ebook_obj.path, "rb") as f:
            # configure for uploads
            opener = urllib2.build_opener(newHTTPHandler())
            opener.addheaders = [
                ('Ogre-key', session_key)
            ]

            # build the post params
            params = {
                'ebook_id': ebook_obj.ebook_id,
                'file_hash': ebook_obj.file_hash,
                'format': ebook_obj.format,
                'ebook': f,
            }
            req = opener.open(
                'http://{}/api/v1/upload'.format(host), params
            )
            if req.code != 200:
                raise UploadError(ebook_obj)

    except (HTTPError, URLError) as e:
        raise UploadError(ebook_obj, inner_excp=e)
    except IOError as e:
        raise UploadError(ebook_obj, inner_excp=e)


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

            for e in errord_list:
                filename = os.path.basename(e.ebook_obj.path.encode('utf-8'))

                with open(e.ebook_obj.path, "rb") as f:
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
