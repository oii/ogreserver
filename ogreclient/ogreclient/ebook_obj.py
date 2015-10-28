from __future__ import absolute_import
from __future__ import unicode_literals

import json
import os
import shutil
import subprocess
import sys

import urllib2
from urllib2 import HTTPError, URLError

from .exceptions import CorruptEbookError, FailedWritingMetaDataError, FailedConfirmError
from .utils import compute_md5, id_generator, make_temp_directory


class EbookObject:
    def __init__(self, config, filepath, file_hash=None, ebook_id=None, size=None, authortitle=None, fmt=None, drmfree=False, skip=False, source=None):
        self.config = config
        self.path = filepath
        self.file_hash = file_hash
        self.ebook_id = ebook_id
        self.size = size
        self.authortitle = authortitle
        if fmt is None:
            _, ext = os.path.splitext(filepath)
            fmt = ext[1:]
        self.format = fmt
        self.drmfree = drmfree
        self.skip = skip
        self.meta = {'source': source}
        self.in_cache = False

    def __unicode__(self):
        if self.meta:
            return '{} {} - {}.{}'.format(
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
        # dictionary indexes defined by SQL query in Cache.get_ebook()
        data = json.loads(cached_obj[2])

        # return an EbookObject
        ebook_obj = EbookObject(
            config=config,
            filepath=path,
            file_hash=cached_obj[0],
            ebook_id=cached_obj[1],
            authortitle=data['authortitle'],
            fmt=data['format'],
            size=data['size'],
            drmfree=bool(cached_obj[3]),
            skip=bool(cached_obj[4]),
        )
        ebook_obj.in_cache = True
        ebook_obj.meta = data['meta']
        return ebook_obj


    def serialize(self, for_cache=False):
        '''
        Serialize the EbookObject for sending or caching
        '''
        data = {
            'file_hash': self.file_hash,
            'format': self.format,
            'size': self.size,
            'dedrm': self.drmfree,
            'meta': self.meta,
        }
        if self.ebook_id is not None:
            data['ebook_id'] = self.ebook_id

        if for_cache:
            # different serialisation for writing the local ogreclient cache
            del(data['file_hash'])
            data['authortitle'] = self.authortitle

        return data


    def compute_md5(self):
        # calculate MD5 of ebook
        md5_tup = compute_md5(self.path)
        self.size, self.file_hash = md5_tup[2], md5_tup[0]
        return self.file_hash, self.size


    def get_metadata(self):
        # extract and parse ebook metadata
        self.meta.update(self._metadata_extract())

        # delimit fields with non-printable chars
        self.authortitle = '{}\u0006{}\u0007{}'.format(
            self.meta['firstname'], self.meta['lastname'], self.meta['title']
        )
        return self.authortitle


    def _metadata_extract(self):
        # get the current filesystem encoding
        fs_encoding = sys.getfilesystemencoding()

        # call ebook-metadata
        proc = subprocess.Popen(
            '{} "{}"'.format(
                self.config['calibre_ebook_meta_bin'], self.path.replace('"', '\\"')
            ).encode(fs_encoding),
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # get raw bytes from stdout and stderr
        out_bytes, err_bytes = proc.communicate()

        if err_bytes.find('EPubException') > 0:
            raise CorruptEbookError(self, err_bytes)

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

                is_amazon_format = self.config['definitions'][fmt[1:]][1]
                if is_amazon_format:
                    # extract the ogre_id which may be embedded into the tags field
                    if 'ogre_id' in meta['tags']:
                        tags = meta['tags'].split(', ')
                        for j in reversed(xrange(len(tags))):
                            if 'ogre_id' in tags[j]:
                                self.ebook_id = tags[j][8:]
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
                        self.ebook_id = ident[8:].strip()

                # clean up mixed ASIN tags
                if 'mobi-asin' in meta.keys() and 'asin' not in meta.keys():
                    meta['asin'] = meta['mobi-asin']
                    del(meta['mobi-asin'])
                elif 'mobi-asin' in meta.keys() and 'asin' in meta.keys() and meta['asin'] == meta['mobi-asin']:
                    del(meta['mobi-asin'])

                continue

        if not meta:
            raise CorruptEbookError(self, 'Failed extracting from {}'.format(self.path))

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


    def add_ogre_id_tag(self, ebook_id, session_key):
        self.ebook_id = ebook_id

        # ebook file format
        fmt = os.path.splitext(self.path)[1]

        with make_temp_directory() as temp_dir:
            # copy the ebook to a temp file
            tmp_name = '{}{}'.format(os.path.join(temp_dir, id_generator()), fmt)
            shutil.copy(self.path, tmp_name)

            try:
                is_amazon_format = self.config['definitions'][fmt[1:]][1]
                if is_amazon_format:
                    # append ogre's ebook_id to the ebook's comma-separated tags field
                    # as they don't support --identifier
                    if 'tags' in self.meta and self.meta['tags']:
                        new_tags = 'ogre_id={}, {}'.format(ebook_id, self.meta['tags'])
                    else:
                        new_tags = 'ogre_id={}'.format(ebook_id)

                    # write ogre_id to --tags
                    subprocess.check_output(
                        [self.config['calibre_ebook_meta_bin'], tmp_name, '--tags', new_tags],
                        stderr=subprocess.STDOUT
                    )
                else:
                    # write ogre_id to --identifier
                    subprocess.check_output(
                        [self.config['calibre_ebook_meta_bin'], tmp_name, '--identifier', 'ogre_id:{}'.format(ebook_id)],
                        stderr=subprocess.STDOUT
                    )

                # calculate new MD5 after updating metadata
                new_hash = compute_md5(tmp_name)[0]

                # ping ogreserver with the book's new hash
                req = urllib2.Request(
                    url='http://{}/api/v1/confirm'.format(self.config['host']),
                    data=json.dumps({
                        'file_hash': self.file_hash,
                        'new_hash': new_hash
                    }),
                    headers={
                        'Content-type': 'application/json',
                        'Ogre-key': session_key
                    },
                )
                resp = urllib2.urlopen(req)
                data = resp.read()

                if data == 'ok':
                    # move file back into place
                    shutil.copy(tmp_name, self.path)
                    self.file_hash = new_hash
                    return new_hash

                elif data == 'fail':
                    raise FailedConfirmError(self, "Server said 'no'")
                elif data == 'same':
                    raise FailedConfirmError(self, "Server said 'same'")
                else:
                    raise FailedConfirmError(self, 'Unknown response from server!')

            except subprocess.CalledProcessError as e:
                raise FailedWritingMetaDataError(self, str(e))

            except (HTTPError, URLError) as e:
                raise FailedConfirmError(self, str(e))


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
                    new_tags = 'OGRE-DeDRM, {}'.format(existing_tags)
                else:
                    new_tags = 'OGRE-DeDRM'

                # write DeDRM to --tags
                subprocess.check_output(
                    [self.config['calibre_ebook_meta_bin'], tmp_name, '--tags', new_tags],
                    stderr=subprocess.STDOUT
                )

                # move file back into place
                shutil.copy(tmp_name, self.path)

                self.drmfree = True

            except subprocess.CalledProcessError as e:
                raise FailedWritingMetaDataError(self, str(e))
