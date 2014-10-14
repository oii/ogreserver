from __future__ import absolute_import
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

from .definitions import RANKED_EBOOK_FORMATS

from .exceptions import AuthDeniedError, AuthError, NoEbooksError, DuplicateEbookFoundError
from .exceptions import BaconError, MushroomError, SpinachError, CorruptEbookError
from .exceptions import FailedWritingMetaDataError, FailedConfirmError, FailedDebugLogsError


def authenticate(host, username, password):
    try:
        # authenticate the user; retrieve an session_key for subsequent requests
        params = urllib.urlencode({
            'username': username,
            'password': password
        })
        req = urllib2.Request(url='http://{}/auth'.format(host), data=params)
        f = urllib2.urlopen(req)
        return f.read()

    except HTTPError as e:
        if e.getcode() == 403:
            raise AuthDeniedError
        else:
            raise AuthError(str(e))
    except URLError as e:
        raise AuthError(str(e))


def sync(config, prntr):
    # authenticate user and generate session API key
    session_key = authenticate(config['host'], config['username'], config['password'])

    # 1) find ebooks in config['ebook_home'] on local machine
    ebooks_dict, errord_list = search_for_ebooks(config, prntr)

    if len(errord_list) > 0:
        prntr.p(u'Errors occurred during scan:')
        for message, e in errord_list.values():
            prntr.e(u'{}'.format(unicode(message)), excp=e)

    # 2) remove DRM
    if config['no_drm'] is False:
        errord_list = clean_all_drm(config, prntr, ebooks_dict)

        if len(errord_list) > 0:
            prntr.e(u'Errors occurred during decryption:')
            for message, e in errord_list.values():
                prntr.e(u'{}'.format(unicode(message)), excp=e)

    # 3) send dict of ebooks / md5s to ogreserver
    response = sync_with_server(config, prntr, session_key, ebooks_dict)

    if not response['ebooks_to_upload'] and not response['ebooks_to_update']:
        if not errord_list:
            prntr.p('Finished, nothing to do.')
        else:
            if config['debug'] is False:
                prntr.e('Finished with errors. Re-run with --debug to send logs to OGRE')
            else:
                prntr.e('Finished with errors.')
                send_logs(prntr, config['host'], session_key, errord_list)
        return

    prntr.p(u'Come on sucker, lick my battery')

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


def search_for_ebooks(config, prntr):
    ebooks = []

    # let the user know something is happening
    prntr.p(u'Searching for ebooks.. ', nonl=True)

    # process ebooks in a directory
    def _process_ebook_dir(root, files):
        for filename in files:
            fn, ext = os.path.splitext(filename)
            if ext[1:] in RANKED_EBOOK_FORMATS.keys() and fn[0:2] != '._':
                ebooks.append(
                    (os.path.join(root, filename), fn, ext[1:])
                )

    # search for ebooks in all provider dirs & ebook_home
    for provider_dir in config['providers'].values() + [config['ebook_home']]:
        if config['debug']:
            prntr.p(u'Searching {}'.format(provider_dir))

        for root, _, files in os.walk(provider_dir):
            _process_ebook_dir(root, files)

    i = 0
    prntr.p(u'Discovered {} files'.format(len(ebooks)))
    if len(ebooks) == 0:
        raise NoEbooksError

    prntr.p(u'Scanning ebook meta data and checking DRM..')
    ebooks_dict = {}
    errord_list = {}

    for item in ebooks:
        ebook_obj = EbookObject(
            config=config,
            filepath=item[0],
            filename=item[1],
            fmt=item[2],
            owner=config['username'],
        )
        # calculate MD5 of ebook
        ebook_obj.compute_md5()

        try:
            # extract ebook metadata and build key
            # books are indexed by 'authortitle' to handle multiple copies of the same book
            authortitle = ebook_obj.get_metadata()

        except CorruptEbookError as e:
            # record books which failed during search
            errord_list[ebook_obj.path] = e

            # add book to the cache as a skip
            config['ebook_cache'].set_ebook(ebook_obj.path, skip=True)

            # skip books which can't have metadata extracted
            continue

        # check for duplicated authortitle/format
        if authortitle in ebooks_dict.keys() and ebooks_dict[authortitle]['format'] == ebook_obj.format:
            # warn user on error stack
            errord_list[ebook_obj.path] = DuplicateEbookFoundError
        else:
            # new ebook, or different format of duplicate ebook found
            write = False

            if authortitle in ebooks_dict.keys():
                # compare the rank of the format already found against this one
                existing_rank = RANKED_EBOOK_FORMATS[ebooks_dict[authortitle]['format']]
                new_rank = RANKED_EBOOK_FORMATS[ebook_obj.format]

                # lower is better
                if new_rank < existing_rank:
                    write = True
            else:
                # new book found
                write = True

            if write:
                # output dictionary for sending to ogreserver
                ebooks_dict[authortitle] = ebook_obj.to_dict()

                # add book to the cache
                config['ebook_cache'].set_ebook(ebook_obj.path, ebook_obj.file_hash, ebooks_dict[authortitle])
            else:
                # add book to the cache as a skip
                config['ebook_cache'].set_ebook(ebook_obj.path, ebook_obj.file_hash, skip=True)

        i += 1
        prntr.progressf(num_blocks=i, total_size=len(ebooks))

    prntr.p(u'Found {} ebooks'.format(len(ebooks_dict)), success=True)

    if len(ebooks_dict) == 0:
        return {}, errord_list

    return ebooks_dict, errord_list


def clean_all_drm(config, prntr, ebooks_dict):
    errord_list = {}

    i = 0
    cleaned = 0

    for authortitle, ebook_data in ebooks_dict.items():
        ebook_data['dedrm'] = False

        try:
            filename, suffix = os.path.splitext(os.path.basename(ebook_data['path']))

            # remove DRM from ebook
            new_filepath, new_filehash, new_filesize = remove_drm_from_ebook(
                config, prntr, ebook_data['path'], ebook_data['file_hash'], suffix
            )

            if new_filepath is not None:
                # update the sync data with the decrypted ebook
                ebook_data['path'] = new_filepath
                ebook_data['file_hash'] = new_filehash
                ebook_data['size'] = new_filesize
                filename, suffix = os.path.splitext(os.path.basename(new_filepath))
                ebook_data['filename'] = filename
                ebook_data['format'] = suffix[1:]
                ebook_data['dedrm'] = True
                cleaned += 1

        except CorruptEbookError as e:
            # record books which failed due to unicode filename issues
            errord_list[ebook_data['path']] = e
            continue

        if config['verbose'] is False:
            i += 1
            prntr.progressf(num_blocks=i, total_size=len(ebooks_dict))

    if config['verbose'] is False:
        prntr.p(u'Cleaned DRM from {} ebooks'.format(cleaned), success=True)

    return errord_list


def remove_drm_from_ebook(config, prntr, filepath, file_hash, suffix):
    if config['debug'] is False or config['use_cache'] is True:
        # attempt load ebook from local cache
        _, drmfree, skip = config['ebook_cache'].get_ebook(filepath, file_hash)

        # return if book marked DRM free in the cache
        if bool(drmfree) is True or bool(skip) is True:
            return None, None, None

    new_filepath = new_filehash = new_filesize = None

    try:
        # decrypt into a temp path
        with make_temp_directory() as ebook_output_path:
            state, decrypted_filepath = decrypt(
                filepath, suffix, config['config_dir'], output_dir=ebook_output_path
            )

            if state == DRM.none:
                # update cache to mark book as drmfree
                config['ebook_cache'].set_ebook(filepath, drmfree=True)

            elif state == DRM.decrypted:
                if config['verbose']:
                    prntr.p(u'DRM removed from {}'.format(filepath), CliPrinter.DEDRM, success=True)

                # create new ebook_obj for decrypted ebook
                ebook_obj = EbookObject(config=config, filepath=decrypted_filepath)
                new_filehash, new_filesize = ebook_obj.compute_md5()

                # add the OGRE DeDRM tag to the decrypted ebook
                ebook_obj.add_dedrm_tag()

                # init OGRE directory in user's ebook dir
                if not os.path.exists(os.path.join(config['ebook_home'], 'ogre')):
                    os.mkdir(os.path.join(config['ebook_home'], 'ogre'))

                # move decrypted book into ebook library
                new_filepath = os.path.join(
                    config['ebook_home'], 'ogre', os.path.basename(decrypted_filepath)
                )
                os.rename(decrypted_filepath, new_filepath)

                if config['verbose']:
                    prntr.p(u'Decrypted book moved to {}'.format(new_filepath), CliPrinter.DEDRM, success=True)

                # mark decrypted book as drmfree=True in cache
                config['ebook_cache'].set_ebook(filepath, new_filehash, drmfree=True)

                # update existing DRM-scuppered as skip=True in cache
                config['ebook_cache'].set_ebook(filepath, skip=True)

            else:
                # mark book as having DRM
                config['ebook_cache'].set_ebook(filepath, file_hash, drmfree=False)

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

    return new_filepath, new_filehash, new_filesize


def sync_with_server(config, prntr, session_key, ebooks_dict):
    try:
        # post json dict of ebook data
        req = urllib2.Request(
            url='http://{}/post/{}'.format(
                config['host'],
                urllib.quote_plus(session_key)
            ),
            headers={'Content-Type': 'application/json'},
        )
        req.add_data(json.dumps(ebooks_dict))
        resp = urllib2.urlopen(req)
        data = resp.read()

        response = json.loads(data)

    except ValueError as e:
        raise BaconError(str(e))
    except (HTTPError, URLError) as e:
        raise MushroomError(str(e))

    # display server messages
    for msg in response['messages']:
        if len(msg) == 2:
            prntr.p("{0} {1}".format(msg[0], msg[1]), CliPrinter.RESPONSE)
        else:
            prntr.p(msg, CliPrinter.RESPONSE)

    return response


def update_local_metadata(config, prntr, session_key, ebooks_dict, ebooks_to_update):
    success, failed = 0, 0

    # update any books with ogre_id supplied from ogreserver
    for file_hash, item in ebooks_to_update.items():
        # find this book in the scan data
        for authortitle, ebook_data in ebooks_dict.items():
            if file_hash == ebook_data['file_hash']:
                try:
                    # create new ebook_obj for ebook to be updated
                    ebook_obj = EbookObject(
                        config=config,
                        filepath=ebook_data['path'],
                        file_hash=ebook_data['file_hash']
                    )

                    # update the metadata on the ebook, and communicate that to ogreserver
                    new_file_hash = ebook_obj.add_ogre_id_tag(
                        item['ebook_id'],
                        ebook_data['tags'] if 'tags' in ebook_data else None,
                        session_key
                    )

                    # update file hash in ogreclient data
                    ebook_data['file_hash'] = new_file_hash
                    success += 1
                    if config['verbose']:
                        prntr.p(u'Wrote OGRE_ID to {}'.format(ebook_data['path']))

                    # write to ogreclient cache
                    config['ebook_cache'].set_ebook(ebook_data['path'], new_file_hash)

                except (FailedWritingMetaDataError, FailedConfirmError) as e:
                    prntr.e(u'Failed saving OGRE_ID in {}'.format(ebook_data['path']), excp=e)
                    failed += 1

    if success > 0:
        prntr.p(u'Updated {} ebooks'.format(success), success=True)
    if failed > 0:
        prntr.e(u'Failed updating {} ebooks'.format(failed))


def upload_ebooks(config, prntr, session_key, ebooks_dict, ebooks_to_upload):
    if len(ebooks_to_upload) == 0:
        return

    # grammatically correct messages are nice
    plural = 's' if len(ebooks_to_upload) > 1 else ''

    prntr.p(u'Uploading {} file{}. Go make a brew.'.format(len(ebooks_to_upload), plural))

    success, failed, i = 0, 0, 0

    # upload each requested by the server
    for upload in ebooks_to_upload:
        # iterate all user's found books
        for authortitle, ebook_data in ebooks_dict.items():
            if upload['file_hash'] == ebook_data['file_hash']:
                try:
                    upload_single_book(
                        config['host'],
                        session_key,
                        ebook_data['path'],
                        upload,
                    )
                    success += 1

                except SpinachError as e:
                    prntr.e(u'Failed uploading {}'.format(ebook_data['path']), excp=e)
                    failed += 1

        i += 1
        prntr.progressf(num_blocks=i, total_size=len(ebooks_to_upload))

    if success > 0:
        prntr.p(u'Completed {} uploads'.format(success), success=True)
    if failed > 0:
        prntr.e(u'Failed uploading {} ebooks'.format(failed))


def upload_single_book(host, session_key, filepath, upload_obj):
    try:
        with open(filepath, "rb") as f:
            # configure for uploads
            opener = urllib2.build_opener(newHTTPHandler())

            # build the post params
            params = {
                'ebook_id': upload_obj['ebook_id'],
                'file_hash': upload_obj['file_hash'],
                'format': upload_obj['format'],
                'ebook': f,
            }
            req = opener.open(
                "http://{0}/upload/{1}".format(host, urllib.quote_plus(session_key)), params
            )
            return req.read()

    except (HTTPError, URLError), e:
        raise SpinachError(str(e))
    except IOError, e:
        pass


def send_logs(prntr, host, session_key, errord_list):
    try:
        # post all logs to ogreserver
        req = urllib2.Request(
            url='http://{}/post-logs/{}'.format(host, urllib.quote_plus(session_key)),
            headers={'Content-Type': 'application/json'},
        )
        req.add_data(u'\n'.join(prntr.logs).encode('utf-8'))
        resp = urllib2.urlopen(req)
        data = resp.read()

        if data != 'ok':
            raise FailedDebugLogsError('Failed storing the logs, please report this.')
        else:
            prntr.p(u'Uploaded logs to OGRE')

        # upload all books which failed
        if errord_list:
            prntr.p(u'Uploaded failed books to OGRE for debug..')

            opener = urllib2.build_opener(newHTTPHandler())

            i = 0

            for filepath in errord_list.keys():
                filename = os.path.basename(filepath.encode('utf-8'))

                with open(filepath, "rb") as f:
                    # post the file contents
                    req = opener.open(
                        'http://{}/upload-errord/{}/{}'.format(
                            host,
                            urllib.quote_plus(session_key),
                            urllib.quote_plus(filename),
                        ),
                        {'ebook': f},
                    )
                    # ignore failures here
                    req.read()

                i += 1
                prntr.progressf(num_blocks=i, total_size=len(errord_list))

    except (HTTPError, URLError) as e:
        raise FailedDebugLogsError(str(e))
