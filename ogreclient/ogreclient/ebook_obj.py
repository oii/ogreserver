from __future__ import absolute_import

import json
import os
import shutil
import subprocess
import sys

import urllib
import urllib2
from urllib2 import HTTPError, URLError

from .definitions import MOBI_FORMATS
from .exceptions import CorruptEbookError, FailedWritingMetaDataError, FailedConfirmError
from .utils import compute_md5, id_generator, make_temp_directory


class EbookObject:
    def __init__(self, config, filepath, size=None, file_hash=None, authortitle=None, fmt=None, drmfree=False, skip=False):
        self.config = config
        self.path = filepath
        self.size = size
        self.file_hash = file_hash
        self.authortitle = authortitle
        self.format = fmt
        self.drmfree = drmfree
        self.skip = skip
        self.meta = {}
        self.in_cache = False

    def __unicode__(self):
        if self.meta:
            return u'{} {} - {}.{}'.format(
                self.meta['firstname'],
                self.meta['lastname'],
                self.meta['title'],
                self.format
            )
        else:
            return unicode(os.path.splitext(os.path.basename(self.path))[0])

    def __str__(self):
        return unicode(self).encode('utf-8')


    @staticmethod
    def deserialize(config, path, cached_obj):
        '''
        Deserialize from a cached object into an EbookObject
        '''
        # parse the data object from the cache entry
        data = json.loads(cached_obj[1])

        # return an EbookObject
        ebook_obj = EbookObject(
            config=config,
            filepath=path,
            file_hash=cached_obj[0],
            authortitle=data['authortitle'],
            fmt=data['format'],
            drmfree=bool(cached_obj[2]),
            skip=bool(cached_obj[3]),
        )
        ebook_obj.in_cache = True
        ebook_obj.meta = data['meta']
        return ebook_obj


    def serialize(self, for_cache=False):
        '''
        Serialize the EbookObject for sending or caching
        '''
        data = {
            u'path': self.path,
            u'format': self.format,
            u'size': self.size,
            u'file_hash': self.file_hash,
            u'dedrm': self.drmfree,
            u'meta': self.meta
        }
        if for_cache:
            # different serialisation for writing the local ogreclient cache
            del(data['path'])
            del(data['file_hash'])
            data['authortitle'] = self.authortitle
        return data


    def compute_md5(self):
        # calculate MD5 of ebook
        md5_tup = compute_md5(self.path, buf_size=524288)
        self.size, self.file_hash = md5_tup[2], md5_tup[0]
        return self.file_hash, self.size


    def get_metadata(self):
        # extract and parse ebook metadata
        self.meta = self._metadata_extract()

        # delimit fields with non-printable chars
        self.authortitle = u'{}\u0006{}\u0007{}'.format(
            self.meta['firstname'], self.meta['lastname'], self.meta['title']
        )
        return self.authortitle


    def _metadata_extract(self):
        # get the current filesystem encoding
        fs_encoding = sys.getfilesystemencoding()

        # call ebook-metadata
        proc = subprocess.Popen(
            '{} "{}"'.format(self.config['calibre_ebook_meta_bin'], self.path.encode(fs_encoding)),
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
        fmt = os.path.splitext(self.path)[1]

        for line in extracted.splitlines():
            # extract the simple metadata
            for prop in ('title', 'publisher'):
                if line.lower().startswith(prop):
                    meta[prop] = line[line.find(':')+1:].strip()
                    continue

            # rename published to publish_date
            if line.lower().startswith('published'):
                meta['publish_date'] = line[line.find(':')+1:].strip()
                continue

            if 'Tags' in line:
                meta['tags'] = line[line.find(':')+1:].strip()

                # extract DeDRM tag and remove from list
                if 'OGRE-DeDRM' in meta['tags']:
                    tags = meta['tags'].split(', ')
                    for j in reversed(xrange(len(tags))):
                        if 'OGRE-DeDRM' in tags[j]:
                            self.drmfree = True
                            del(tags[j])
                    meta['tags'] = ', '.join(tags)

                # extract the ogre_id which may be embedded into the tags field
                if fmt[1:] in MOBI_FORMATS:
                    if 'ogre_id' in meta['tags']:
                        tags = meta['tags'].split(', ')
                        for j in reversed(xrange(len(tags))):
                            if 'ogre_id' in tags[j]:
                                meta['ebook_id'] = tags[j][8:]
                                del(tags[j])
                        meta['tags'] = ', '.join(tags)
                continue

            if 'Author' in line:
                # derive firstname & lastname from author tag
                author = line[line.find(':')+1:].strip()
                meta['firstname'], meta['lastname'] = EbookObject._parse_author(author)
                continue

            if 'Identifiers' in line:
                identifiers = line[line.find(':')+1:].strip()
                for ident in identifiers.split(','):
                    ident = ident.strip()
                    if ident.startswith('isbn'):
                        meta['isbn'] = ident[5:].strip()
                        continue
                    if ident.startswith('asin'):
                        meta['asin'] = ident[5:].strip()
                        continue
                    if ident.startswith('mobi-asin'):
                        meta['mobi-asin'] = ident[10:].strip()
                        continue
                    if ident.startswith('uri'):
                        meta['uri'] = ident[4:].strip()
                        continue
                    if ident.startswith('epubbud'):
                        meta['epubbud'] = ident[7:].strip()
                        continue
                    if ident.startswith('ogre_id'):
                        meta['ebook_id'] = ident[8:].strip()

                # clean up mixed ASIN tags
                if 'mobi-asin' in meta.keys() and 'asin' not in meta.keys():
                    meta['asin'] = meta['mobi-asin']
                    del(meta['mobi-asin'])
                elif 'mobi-asin' in meta.keys() and 'asin' in meta.keys() and meta['asin'] == meta['mobi-asin']:
                    del(meta['mobi-asin'])

                continue

        if not meta:
            raise CorruptEbookError('Failed extracting from {}'.format(self.path))

        return meta


    @staticmethod
    def _parse_author(author):
        if type(author) is not unicode:
            # convert from UTF-8
            author = author.decode('utf8')

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


    def add_ogre_id_tag(self, ogre_id, session_key):
        # ebook file format
        fmt = os.path.splitext(self.path)[1]

        with make_temp_directory() as temp_dir:
            # copy the ebook to a temp file
            tmp_name = '{}{}'.format(os.path.join(temp_dir, id_generator()), fmt)
            shutil.copy(self.path, tmp_name)

            try:
                if fmt[1:] in MOBI_FORMATS:
                    # append ogre's ebook_id to the ebook's comma-separated tags field
                    # as they don't support --identifier
                    if 'tags' in self.meta and self.meta['tags']:
                        new_tags = u'ogre_id={}, {}'.format(ogre_id, self.meta['tags'])
                    else:
                        new_tags = u'ogre_id={}'.format(ogre_id)

                    # write ogre_id to --tags
                    subprocess.check_output(
                        [self.config['calibre_ebook_meta_bin'], tmp_name, '--tags', new_tags],
                        stderr=subprocess.STDOUT
                    )
                else:
                    # write ogre_id to --identifier
                    subprocess.check_output(
                        [self.config['calibre_ebook_meta_bin'], tmp_name, '--identifier', 'ogre_id:{}'.format(ogre_id)],
                        stderr=subprocess.STDOUT
                    )

                # calculate new MD5 after updating metadata
                new_hash = compute_md5(tmp_name)[0]

                # ping ogreserver with the book's new hash
                req = urllib2.Request(
                    url='http://{}/confirm/{}'.format(self.config['host'], urllib.quote_plus(session_key))
                )
                req.add_data(urllib.urlencode({
                    'file_hash': self.file_hash,
                    'new_hash': new_hash
                }))
                resp = urllib2.urlopen(req)
                data = resp.read()

                if data == 'ok':
                    # move file back into place
                    shutil.copy(tmp_name, self.path)
                    self.file_hash = new_hash
                    return new_hash
                else:
                    raise FailedConfirmError("Server said 'no'")

            except subprocess.CalledProcessError as e:
                raise FailedWritingMetaDataError(str(e))

            except (HTTPError, URLError) as e:
                raise FailedConfirmError(str(e))


    def add_dedrm_tag(self):
        # get the existing tags from metadata
        self.get_metadata()
        existing_tags = self.meta['tags'] if 'tags' in self.meta else None

        if existing_tags is not None and 'OGRE-DeDRM' in existing_tags:
            return

        with make_temp_directory() as temp_dir:
            # ebook file format
            fmt = os.path.splitext(self.path)[1]

            # copy the ebook to a temp file
            tmp_name = '{}{}'.format(os.path.join(temp_dir, id_generator()), fmt)
            shutil.copy(self.path, tmp_name)

            try:
                # append DeDRM to the tags list
                if existing_tags is not None and len(existing_tags) > 0:
                    new_tags = u'OGRE-DeDRM, {}'.format(existing_tags)
                else:
                    new_tags = u'OGRE-DeDRM'

                # write DeDRM to --tags
                subprocess.check_output(
                    [self.config['calibre_ebook_meta_bin'], tmp_name, '--tags', new_tags],
                    stderr=subprocess.STDOUT
                )

                # move file back into place
                shutil.copy(tmp_name, self.path)

                self.drmfree = True

            except subprocess.CalledProcessError as e:
                raise FailedWritingMetaDataError(str(e))
