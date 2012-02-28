from ogreserver import app, boto, datetime

from ogreserver.models.test.factory import Factory
from ogreserver.models.log import Log

from boto.exception import S3ResponseError

import os, hashlib, subprocess


class DataStore():

    def __init__(self, user):
        self.user = user

    def update_library(self, ebooks):
        new_ebook_count = 0
        bookdb = Factory.connect_bookdb()
        formatdb = Factory.connect_formatdb()
        versiondb = Factory.connect_versiondb()

        for authortitle in ebooks.keys():
            # check for this in the library
            b = bookdb.get_item(authortitle)

            if b is None:
                self.create_book_entry(authortitle, ebooks[authortitle].keys())

                # create format and version entries
                for fmt in ebooks[authortitle].keys():
                    self.create_format_entry(authortitle, fmt)
                    key = self.create_version_entry(authortitle, fmt, 1, ebooks[authortitle][fmt]['size'], ebooks[authortitle][fmt]['filehash'])
                    new_ebook_count += 1

            # update an existing book
            else:
                # add user to set of owners
                if self.user.username not in b['users']:
                    b.add_value("users", self.user.username)

                # check if supplied formats already exist
                for fmt in ebooks[authortitle].keys():
                    f = formatdb.get_item(authortitle+fmt)

                    # append to the set of this book's formats
                    if fmt not in b['formats']:
                        b.add_value("formats", fmt)

                    if f is None:
                        # create the new format and version entries
                        self.create_format_entry(authortitle, fmt)
                        key = self.create_version_entry(authortitle, fmt, 1, ebooks[authortitle][fmt]['size'], ebooks[authortitle][fmt]['filehash'])
                        new_ebook_count += 1
                    else:
                        # format exists; ensure this exact version hasn't already been uploaded
                        if self.check_version_exists(ebooks[authortitle][fmt]['filehash']):
                            # increment the count of different versions of this format
                            f['version_count'] = int(f['version_count']) + 1
                            f.save()

                            # create the new version entry
                            key = self.create_version_entry(authortitle, fmt, f['version_count'], ebooks[authortitle][fmt]['size'], ebooks[authortitle][fmt]['filehash'])
                            new_ebook_count += 1
                        else:
                            print "ignoring exact duplicate %s" % authortitle

        return new_ebook_count


    def create_book_entry(self, authortitle, formats):
        bookdb = Factory.connect_bookdb()
        key = hashlib.md5(authortitle).hexdigest()
        b = bookdb.new_item(authortitle)
        b.add_value("authortitle", authortitle)
        b.add_value("users", self.user.username)
        b.add_value("formats", formats)
        b.add_value("sdbkey", key)
        b.save()
        return key

    def create_format_entry(self, authortitle, fmt):
        formatdb = Factory.connect_formatdb()
        key = hashlib.md5(authortitle + fmt).hexdigest()
        f = formatdb.new_item(key)
        f.add_value("authortitle", authortitle)
        f.add_value("format", fmt)
        f.add_value("version_count", 1)
        f.add_value("sdbkey", key)
        f.save()
        return key

    def create_version_entry(self, authortitle, fmt, version, size, filehash):
        versiondb = Factory.connect_versiondb()
        key = hashlib.md5(authortitle + '-' + str(version) + fmt).hexdigest()
        v = versiondb.new_item(key)
        v.add_value("authortitle", authortitle)
        v.add_value("format", fmt)
        v.add_value("user", self.user.username)
        v.add_value("size", size)
        v.add_value("filehash", filehash)
        v.add_value("sdbkey", key)
        v.save()
        return key

    def check_version_exists(self, filehash):
        sdb = Factory.connect_sdb()
        rs = sdb.select("ogre_versions", "select filehash from ogre_versions where filehash = '%s'" % filehash)
        return (len(rs) > 0)

    def set_uploaded(self, sdbkey):
        versiondb = Factory.connect_versiondb()
        v = versiondb.get_item(sdbkey)
        v.add_value("uploaded", True)
        v.save()

    def set_dedrm_flag(self, sdbkey):
        versiondb = Factory.connect_versiondb()
        v = versiondb.get_item(sdbkey)
        v.add_value("dedrm", True)
        v.save()

    def store_ebook(self, sdbkey, filehash, filepath):
        # connect to S3
        bucket = Factory.connect_s3()
        k = Factory.get_key(bucket)
        k.key = sdbkey

        # calculate uploaded file md5
        f = open(filepath, "rb")
        md5_tup = k.compute_md5(f)
        f.close()

        # error check uploaded file
        if filehash != md5_tup[0]:
            # TODO logging
            print 'upload corrupt!'
        else:
            try:
                # check for DeDRM meta tag
                meta = subprocess.Popen(['ebook-meta', filepath], stdout=subprocess.PIPE).communicate()[0]
                if "Tags                : DeDRM" in meta:
                    Log.create(self.user.id, "DEDRM", 1)
                    self.set_dedrm_flag(sdbkey)

                # push file to S3
                k.set_contents_from_filename(filepath, None, False, None, 10, None, md5_tup)

                # mark ebook as saved
                self.set_uploaded(sdbkey)

            except S3ResponseError as e:
                # TODO log
                print 'MD5 error at S3'

        # always delete local file
        os.remove(filepath)

    def find_missing_books(self):
        # query for books which have no uploaded file
        sdb = Factory.connect_sdb()
        return sdb.select("ogre_versions", "select sdbkey, filehash, format from ogre_versions where uploaded is null and user = '%s'" % self.user.username)

    def update_timestamp(self):
        bookdb = Factory.connect_bookdb()

        # set library updated timestamp
        meta = bookdb.get_item("meta")
        if meta == None:
            meta = bookdb.new_item("meta")

        meta['updated'] = datetime.utcnow().isoformat()
        meta.save()


