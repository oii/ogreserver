from __future__ import absolute_import
from __future__ import division

import codecs
import datetime
import json
import os
import shutil
import subprocess
import sys

import urllib
import urllib2
from urllib2 import HTTPError, URLError
from .urllib2_file import newHTTPHandler

from .utils import compute_md5
from .utils import id_generator
from .utils import make_temp_directory
from .printer import CliPrinter, DummyPrinter
from .dedrm import decrypt, DRM, DeDrmMissingError

from .exceptions import AuthDeniedError, AuthError, NoEbooksError
from .exceptions import BaconError, MushroomError, SpinachError, CorruptEbookError
from .exceptions import FailedWritingMetaDataError, FailedConfirmError, FailedDebugLogsError


OGRESERVER = "ogre.oii.yt"

RANKED_EBOOK_FORMATS = {
    'mobi': 1,
    'azw': 2,
    'azw3': 3,
    'azw4': 4,
    'pdf': 5,
    'epub': 6,
    'pdb': 7,
    'azw1': 8,
    'tpz': 9,
}

MOBI_FORMATS = ('mobi', 'azw', 'azw3', 'azw4', 'azw1')


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


def sync(config):
    # authenticate user and generate session API key
    session_key = authenticate(config['host'], config['username'], config['password'])

    if config['quiet'] is True:
        prntr = DummyPrinter()
    else:
        prntr = CliPrinter(start=datetime.datetime.now(), debug=config['debug'])

        # set printer to log everything for later dispatch to ogreserver
        if config['debug'] is True:
            prntr.log_output(True)

    # 1) find ebooks in config['ebook_home'] on local machine
    ebooks_dict, errord_list = search_for_ebooks(config, prntr)

    # 2) send dict of ebooks / md5s to ogreserver
    response = sync_with_server(config, prntr, session_key, ebooks_dict)

    if not response['ebooks_to_upload'] and not response['ebooks_to_update']:
        prntr.p('Finished')
        return

    # 3) set ogre_id in metadata of each sync'd ebook
    update_local_metadata(
        config, prntr, session_key, ebooks_dict, response['ebooks_to_update']
    )

    # 4) upload the ebooks requested by ogreserver
    upload_ebooks(
        config, prntr, session_key, ebooks_dict, response['ebooks_to_upload']
    )

    # 5) send a log of all events, and upload bad books
    if config['debug'] is True:
        send_logs(prntr, config['host'], session_key, errord_list)


def search_for_ebooks(config, prntr):
    if config['config_dir'] is not None:
        # load the user's database of previously scanned ebooks
        if os.path.exists(config['ebook_cache_path']):
            with codecs.open(config['ebook_cache_path'], 'r', 'utf-8') as f:
                data = f.read()

        # setup temporary cache path
        ebook_cache_temp_path = os.path.join(
            config['config_dir'],
            '{}.tmp'.format(config['ebook_cache_path'])
        )

    ebooks = []

    # let the user know something is happening
    prntr.p(u'Searching for ebooks.. ', nonl=True)

    # get the current filesystem encoding
    fs_encoding = sys.getfilesystemencoding()

    # a relatively quick search for all ebooks
    for root, dirs, files in os.walk(config['ebook_home']):
        for filename in files:
            # decode filename according to local fs encoding
            filename = codecs.decode(filename, fs_encoding)

            fn, ext = os.path.splitext(filename)
            if ext[1:] in RANKED_EBOOK_FORMATS.keys() and fn[0:2] != '._':
                filepath = os.path.join(root, filename)
                md5_tup = compute_md5(filepath)
                ebooks.append(
                    (filepath, fn, ext, md5_tup[2], md5_tup[0])
                )

    i = 0
    total = len(ebooks)
    prntr.p(u'Discovered {} files'.format(total))
    if total == 0:
        raise NoEbooksError()

    prntr.p(u'Scanning ebook meta data and checking DRM..')
    ebooks_dict = {}
    errord_list = []

    # now parse all book meta data; building a complete dataset
    for item in ebooks:
        # create readable variable names
        filepath = item[0]
        filename = item[1]
        suffix = item[2]
        filesize = item[3]
        file_hash = item[4]

        if config['no_drm'] is False:
            try:
                # decrypt into a temp path
                with make_temp_directory() as ebook_convert_path:
                    state, out = decrypt(filepath, suffix, ebook_convert_path, config['config_dir'])

                if config['verbose']:
                    if state == DRM.none:
                        prntr.p(u'{}'.format(filepath), CliPrinter.NONE)
                    elif state == DRM.decrypted:
                        prntr.p(u'{}'.format(filepath), CliPrinter.DEDRM, success=True)
                    elif state == DRM.wrong_key:
                        prntr.e(u'{}'.format(filepath), CliPrinter.WRONG_KEY)
                    elif state == DRM.failed:
                        prntr.e(u'{}'.format(filepath), CliPrinter.DEDRM,
                            extra=' '.join([l.strip() for l in out])
                        )
                    elif state == DRM.corrupt:
                        prntr.e(u'{}'.format(filepath), CliPrinter.CORRUPT)
                    else:
                        prntr.p(u'{}\t{}'.format(filepath, out), CliPrinter.UNKNOWN)

            except DeDrmMissingError:
                continue
            except UnicodeDecodeError as e:
                # record books which failed during search
                errord_list.append(filepath)
                prntr.e(u"Couldn't decode {}. This will be reported.".format(os.path.basename(filepath)), excp=e)
                continue
            except Exception as e:
                prntr.e(u'Fatal Exception on {}'.format(filepath), excp=e)
                continue

        meta = {}

        try:
            # extract and parse ebook metadata
            meta = metadata_extract(config['calibre_ebook_meta_bin'], filepath=filepath)
        except CorruptEbookError as e:
            # record books which failed during search
            errord_list.append(filepath)

            # skip books which can't have metadata extracted
            if config['verbose']:
                prntr.e(u'{}{}'.format(filename, suffix), CliPrinter.CORRUPT, excp=e)
            continue

        # books are indexed by 'authortitle' to handle multiple copies of the same book
        # delimit fields with non-printable chars
        authortitle = u'{}\u0006{}\u0007{}'.format(meta['firstname'], meta['lastname'], meta['title'])

        # check for duplicates
        if authortitle in ebooks_dict.keys() and suffix in ebooks_dict[authortitle].keys():
            # TODO warn user on error stack
            pass
        else:
            # another format of same book found
            write = False

            if authortitle in ebooks_dict.keys():
                # compare the rank of the format already found against this one
                existing_rank = RANKED_EBOOK_FORMATS[ebooks_dict[authortitle]['format']]
                new_rank = RANKED_EBOOK_FORMATS[suffix[1:]]

                # lower is better
                if new_rank < existing_rank:
                    write = True
            else:
                # new book found
                write = True

            if write:
                ebooks_dict[authortitle] = {
                    'path': filepath,
                    'filename': filename,
                    'format': suffix[1:],
                    'size': filesize,
                    'file_hash': file_hash,
                    'owner': config['username'],
                }
                # merge all the meta data constructed above
                ebooks_dict[authortitle].update(meta)

                # don't need to send author/title since they're composed into the key
                del(ebooks_dict[authortitle]['firstname'])
                del(ebooks_dict[authortitle]['lastname'])
                del(ebooks_dict[authortitle]['title'])

        if config['verbose'] is False:
            i += 1
            prntr.progressf(num_blocks=i, total_size=total)

    prntr.p(u'Found {} ebooks'.format(len(ebooks_dict)), success=True)

    if len(ebooks_dict) == 0:
        return {}, errord_list

    if config['config_dir'] is not None:
        # write good ebooks into the local ogre cache to skip DRM test next run
        with codecs.open(ebook_cache_temp_path, 'w', 'utf-8') as f_ogre_cache:
            # TODO move this to where the ogre_id gets confirmed
            for authortitle, item in ebooks_dict.items():
                f_ogre_cache.write(u'{}\n'.format(item['path']))

        # move the temp cache onto the real ogre cache
        statinfo = os.stat(ebook_cache_temp_path)
        if statinfo.st_size > 0:
            os.rename(ebook_cache_temp_path, config['ebook_cache_path'])

    return ebooks_dict, errord_list


def sync_with_server(config, prntr, session_key, ebooks_dict):
    prntr.p(u'Come on sucker, lick my battery')

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
        for authortitle in ebooks_dict.keys():
            if file_hash == ebooks_dict[authortitle]['file_hash']:
                try:
                    # update the metadata on the ebook, and communicate that to ogreserver
                    new_file_hash = add_ogre_id_to_ebook(
                        config['calibre_ebook_meta_bin'],
                        file_hash,
                        ebooks_dict[authortitle]['path'],
                        ebooks_dict[authortitle]['tags'] if 'tags' in ebooks_dict[authortitle] else None,
                        item['ebook_id'],
                        config['host'],
                        session_key,
                    )
                    # update file hash in ogreclient data
                    ebooks_dict[authortitle]['file_hash'] = new_file_hash
                    success += 1
                    if config['verbose']:
                        prntr.p(u'Wrote OGRE_ID to {}'.format(ebooks_dict[authortitle]['path']))

                except (FailedWritingMetaDataError, FailedConfirmError) as e:
                    prntr.e(
                        u'Failed saving OGRE_ID in {}'.format(
                            ebooks_dict[authortitle]['path']
                        ), excp=e
                    )
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
        for authortitle in ebooks_dict.keys():
            if upload['file_hash'] == ebooks_dict[authortitle]['file_hash']:
                try:
                    upload_single_book(
                        config['host'],
                        session_key,
                        ebooks_dict[authortitle]['path'],
                        upload,
                    )
                    success += 1

                except SpinachError as e:
                    prntr.e(u'Failed uploading {}'.format(ebooks_dict[authortitle]['path']), excp=e)
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


def metadata_extract(calibre_ebook_meta_bin, filepath):
    # get the current filesystem encoding
    fs_encoding = sys.getfilesystemencoding()

    # call ebook-metadata
    proc = subprocess.Popen(
        '{} "{}"'.format(calibre_ebook_meta_bin, filepath.encode(fs_encoding)),
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    # get raw bytes from stdout and stderr
    out_bytes, err_bytes = proc.communicate()

    if err_bytes.find('EPubException') > 0:
        raise CorruptEbookError(err_bytes)

    # interpret bytes as UTF-8
    extracted = out_bytes.decode('utf-8')

    # initialize all the metadata we attempt to extract
    meta = {}

    # modify behaviour for epub/mobi
    format = os.path.splitext(filepath)[1]

    for line in extracted.splitlines():
        # extract the simple metadata
        for prop in ('title', 'publisher', 'published'):
            if line.lower().startswith(prop):
                meta[prop] = line[line.find(':')+1:].strip()
                continue

        if 'Tags' in line:
            meta['tags'] = line[line.find(':')+1:].strip()

            # extract the ogre_id which may be embedded into the tags field
            if format[1:] in MOBI_FORMATS:
                if 'ogre_id' in meta['tags']:
                    tags = meta['tags'].split(', ')
                    for j in reversed(xrange(len(tags))):
                        if 'ogre_id' in tags[j]:
                            meta['ebook_id'] = tags[j][8:]
                            del(tags[j])
                    meta['tags'] = ', '.join(tags)

            # extract the DeDRM flag
            #if 'DeDRM' in meta['tags']:
            #    import pdb;pdb.set_trace()
            #    tags = meta['tags'].split(', ')
            #    for j in reversed(xrange(len(tags))):
            #        if 'DeDRM' in tags[j]:
            #            meta['dedrm'] = tags[j][6:]
            #            del(tags[j])
            #    meta['tags'] = ', '.join(tags)
            continue

        if 'Author' in line:
            # derive firstname & lastname from author tag
            author = line[line.find(':')+1:].strip()
            meta['firstname'], meta['lastname'] = _parse_author(author)
            continue

        if 'Identifiers' in line:
            identifiers = line[line.find(':')+1:].strip()
            for ident in identifiers.split(','):
                if ident.startswith('isbn'):
                    meta['isbn'] = ident[5:].strip()
                if ident.startswith('mobi-asin'):
                    meta['asin'] = ident[10:].strip()
                if ident.startswith('uri'):
                    meta['uri'] = ident[4:].strip()
                if ident.startswith('epubbud'):
                    meta['epubbud'] = ident[7:].strip()
                if ident.startswith('ogre_id'):
                    meta['ebook_id'] = ident[8:].strip()
            continue

    if not meta:
        raise CorruptEbookError('Failed extracting from {}'.format(filepath))

    # calculate file MD5
    meta['file_hash'] = compute_md5(filepath)[0]
    return meta


def _parse_author(author):
    if type(author) is not unicode:
        # convert from UTF-8
        author = author.decode('UTF-8')

    bracketpos = author.find('[')
    # if square bracket in author, parse the contents of the brackets
    if(bracketpos > -1):
        endbracketpos = author.find(']', bracketpos)
        if endbracketpos > -1:
            author = author[bracketpos+1:endbracketpos].strip()
    else:
        author = author.strip()

    if ',' in author:
        # author containing comma is "surname, firstname"
        names = author.split(',')
        lastname = names[0].strip()
        firstname = ' '.join(names[1:]).strip()
    else:
        names = author.split(' ')
        # assume final part is surname, all other parts are firstname
        firstname = ' '.join(names[:-1]).strip()
        lastname = names[len(names[:-1]):][0].strip()

    return firstname, lastname


def add_ogre_id_to_ebook(calibre_ebook_meta_bin, file_hash, filepath, existing_tags, ogre_id, host, session_key):
    format = os.path.splitext(filepath)[1]

    with make_temp_directory() as temp_dir:
        # copy the ebook to a temp file
        tmp_name = '{}{}'.format(os.path.join(temp_dir, id_generator()), format)
        shutil.copy(filepath, tmp_name)

        try:
            if format[1:] in MOBI_FORMATS:
                # append ogre's ebook_id to the tags list
                if existing_tags is not None and len(existing_tags) > 0:
                    new_tags = u'ogre_id={}, {}'.format(ogre_id, existing_tags)
                else:
                    new_tags = u'ogre_id={}'.format(ogre_id)

                # write ogre_id to --tags
                subprocess.check_output(
                    [calibre_ebook_meta_bin, tmp_name, '--tags', new_tags],
                    stderr=subprocess.STDOUT
                )
            else:
                # write ogre_id to --identifier
                subprocess.check_output(
                    [calibre_ebook_meta_bin, tmp_name, '--identifier', 'ogre_id:{}'.format(ogre_id)],
                    stderr=subprocess.STDOUT
                )

            # calculate new MD5 after updating metadata
            new_hash = compute_md5(tmp_name)[0]

            # ping ogreserver with the book's new hash
            req = urllib2.Request(
                url='http://{}/confirm/{}'.format(host, urllib.quote_plus(session_key))
            )
            req.add_data(urllib.urlencode({
                'file_hash': file_hash,
                'new_hash': new_hash
            }))
            resp = urllib2.urlopen(req)
            data = resp.read()

            if data == 'ok':
                # move file back into place
                shutil.copy(tmp_name, filepath)
                return new_hash
            else:
                raise FailedConfirmError("Server said 'no'")

        except subprocess.CalledProcessError as e:
            raise FailedWritingMetaDataError(str(e))

        except (HTTPError, URLError) as e:
            raise FailedConfirmError(str(e))


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

            for filepath in errord_list:
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
