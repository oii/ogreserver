import datetime
import hashlib
import re

from boto.exception import S3ResponseError

from ogreserver.models.factory import Factory


class DataStore():

    def __init__(self, user):
        self.user = user

    def list(self):
        sdb = Factory.connect_sdb()
        return sdb.select("ogre_books", "select authortitle, sdb_key, users, formats from ogre_books")

    def search(self, s):
        sdb = Factory.connect_sdb()
        return sdb.select("ogre_books", "select authortitle, sdb_key, users, formats from ogre_books where searchtext like '%%%s%%'" % s)

    def update_library(self, ebooks):
        new_ebook_count = 0
        bookdb = Factory.connect_bookdb()

        for authortitle in ebooks.keys():
            try:
                # first check if this exact file has been uploaded before
                found_duplicate = False

                for fmt in ebooks[authortitle].keys():
                    if DataStore.check_ebook_exists(ebooks[authortitle][fmt]['filemd5']) == True:
                        found_duplicate = True
                        # TODO any way we can import meta data from this book?
                        break

                if found_duplicate == True:
                    print "ignoring exact duplicate %s" % authortitle
                    continue

                # check for this book by meta data in the library
                bkey = hashlib.md5(authortitle.encode("UTF-8")).hexdigest()
                b = bookdb.get_item(bkey)

                # create this as a new book
                if b is None:
                    self.create_book_entry(authortitle, ebooks[authortitle].keys())

                    # create format and version entries
                    for fmt in ebooks[authortitle].keys():
                        self.create_version_entry(authortitle, 1, fmt, ebooks[authortitle][fmt]['size'])
                        self.create_format_entry(authortitle, 1, fmt, ebooks[authortitle][fmt]['filemd5'])
                        new_ebook_count += 1

                else:
                    # add another version to the existing book entry
                    next_version = self.get_version_count(authortitle) + 1
                    self.create_version_entry(authortitle, next_version, fmt, ebooks[authortitle][fmt]['size'])
                    self.create_format_entry(authortitle, next_version, fmt, ebooks[authortitle][fmt]['filemd5'])
                    new_ebook_count += 1

                    save_book = False

                    # add user to set of owners
                    if self.user.username not in b['users']:
                        b.add_value("users", self.user.username)
                        save_book = True

                    # append to the set of this book's formats
                    if fmt not in b['formats']:
                        b.add_value("formats", fmt)
                        save_book = True

                    if save_book == True:
                        b.save()

            except Exception as e:
                print "[EXCP] %s" % authortitle
                print "\t%s" % e

        return new_ebook_count


    def create_book_entry(self, authortitle, fmt):
        bookdb = Factory.connect_bookdb()
        key = hashlib.md5(authortitle.encode("UTF-8")).hexdigest()
        b = bookdb.new_item(key)
        b['authortitle'] = authortitle
        b['searchtext'] = authortitle.lower()
        b['users'] = self.user.username
        b['formats'] = fmt
        b['sdb_key'] = key
        b.save()
        return key

    def create_version_entry(self, authortitle, version, fmt, size):
        versiondb = Factory.connect_versiondb()
        key = hashlib.md5(("%s.%s" % (authortitle, version)).encode("UTF-8")).hexdigest()
        v = versiondb.new_item(key)
        v['authortitle'] = authortitle
        v['version'] = version
        v['user'] = self.user.username
        v['size'] = size
        v['original_format'] = fmt
        v['sdb_key'] = key
        v.save()
        return key

    def create_format_entry(self, authortitle, version, fmt, filemd5):
        formatdb = Factory.connect_formatdb()
        key = hashlib.md5(("%s-%s.%s" % (authortitle, version, fmt)).encode("UTF-8")).hexdigest()
        f = formatdb.new_item(key)
        f['authortitle'] = authortitle
        f['version'] = version
        f['user'] = self.user.username
        f['format'] = fmt
        f['filemd5'] = filemd5
        f['sdb_key'] = key
        f.save()
        return key

    @staticmethod
    def get_version_count(authortitle):
        sdb = Factory.connect_sdb()
        rs = sdb.select("ogre_versions", "select version from ogre_versions where authortitle = '%s'" % authortitle)
        return len(rs)

    @staticmethod
    def check_ebook_exists(filemd5):
        sdb = Factory.connect_sdb()
        rs = sdb.select("ogre_formats", "select authortitle, version, fmt from ogre_formats where filemd5 = '%s'" % filemd5)
        return (len(rs) > 0)

    @staticmethod
    def set_uploaded(sdb_key, isit=True):
        formatdb = Factory.connect_formatdb()
        f = formatdb.get_item(sdb_key)
        if isit == False:
            f['uploaded'] = None
        else:
            f['uploaded'] = True
        f.save()

    @staticmethod
    def set_dedrm_flag(sdb_key):
        versiondb = Factory.connect_versiondb()
        v = versiondb.get_item(sdb_key)
        v['dedrm'] = True
        v.save()

    @staticmethod
    def store_ebook(sdb_key, filemd5, filename, filepath):
        # connect to S3
        bucket = Factory.connect_s3()
        k = Factory.get_key(bucket)
        k.key = filename

        # calculate uploaded file md5
        f = open(filepath, "rb")
        md5_tup = k.compute_md5(f)
        f.close()

        # error check uploaded file
        if filemd5 != md5_tup[0]:
            # TODO logging
            raise S3DatastoreError("Upload failed checksum 1")
        else:
            try:
                # TODO time this and print
                # push file to S3
                k.set_contents_from_filename(filepath, {'x-amz-meta-ogre-key': sdb_key}, False, None, 10, 'public-read', md5_tup)

                # mark ebook as saved
                DataStore.set_uploaded(sdb_key)

            except S3ResponseError:
                # TODO log
                raise S3DatastoreError("Upload failed checksum 2")

    @staticmethod
    def generate_filename(title, filemd5, fmt):
        # TODO transpose unicode
        return "%s.%s.%s" % (re.sub("[^a-zA-Z0-9]", "_", title), filemd5[0:6], fmt)

    @staticmethod
    def get_missing_books(username=None, verify_s3=False):
        sdb = Factory.connect_sdb()

        if username is not None:
            if verify_s3 == True:
                rs = sdb.select("ogre_formats", "select sdb_key, authortitle, filemd5, format from ogre_formats where user = '%s'" % username)
            else:
                rs = sdb.select("ogre_formats", "select sdb_key, authortitle, filemd5, format from ogre_formats where uploaded is null and user = '%s'" % username)
        else:
            if verify_s3 == True:
                rs = sdb.select("ogre_formats", "select sdb_key, authortitle, filemd5, format from ogre_formats")
            else:
                rs = sdb.select("ogre_formats", "select sdb_key, authortitle, filemd5, format from ogre_formats where uploaded is null")

        if verify_s3 == True:
            # verify books are on S3
            bucket = Factory.connect_s3()
            for r in rs:
                filename = DataStore.generate_filename(r['authortitle'], r['filemd5'], r['format'])
                k = Factory.get_key(bucket, filename)
                DataStore.set_uploaded(r['sdb_key'], k.exists())
                # TODO update rs when verify=True

        return rs

    @staticmethod
    def update_timestamp():
        bookdb = Factory.connect_bookdb()

        # set library updated timestamp
        meta = bookdb.get_item("meta")
        if meta == None:
            meta = bookdb.new_item("meta")

        meta['updated'] = datetime.datetime.utcnow().isoformat()
        meta.save()


class S3DatastoreError(Exception):
    pass
