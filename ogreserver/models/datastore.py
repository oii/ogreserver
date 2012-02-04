from ogreserver import app, boto, datetime
from boto.s3.key import Key
import os, hashlib


class DataStore():

    def __init__(self, user):
        # create connection to sdb
        self.sdb = boto.connect_sdb(app.config['AWS_ACCESS_KEY'], app.config['AWS_SECRET_KEY'])
        self.bookdb = self.sdb.get_domain("ogre_books")
        self.formatdb = self.sdb.get_domain("ogre_formats")
        self.versiondb = self.sdb.get_domain("ogre_versions")
        self.user = user

    def update_library(self, ebooks):
        for authortitle in ebooks.keys():
            # check for this in the library
            b = self.bookdb.get_item(authortitle)

            if b is None:
                self.create_book_entry(authortitle, ebooks[authortitle].keys())

                # create format and version entries
                for fmt in ebooks[authortitle].keys():
                    self.create_format_entry(authortitle, fmt)
                    key = self.create_version_entry(authortitle, fmt, 1, ebooks[authortitle][fmt]['size'], ebooks[authortitle][fmt]['filehash'])

            # update an existing book
            else:
                # add user to set of owners
                if self.user.username not in b['users']:
                    b.add_value("users", self.user.username)

                # check if supplied formats already exist
                for fmt in ebooks[authortitle].keys():
                    f = self.formatdb.get_item(authortitle+fmt)

                    # append to the set of this book's formats
                    if fmt not in b['formats']:
                        b.add_value("formats", fmt)

                    if f is None:
                        # create the new format and version entries
                        self.create_format_entry(authortitle, fmt)
                        key = self.create_version_entry(authortitle, fmt, 1, ebooks[authortitle][fmt]['size'], ebooks[authortitle][fmt]['filehash'])
                    else:
                        # format exists; ensure this exact version hasn't already been uploaded
                        rs = self.sdb.select("ogre_versions", "select filehash from ogre_versions where filehash = '%s'" % ebooks[authortitle][fmt]['filehash'])
                        if len(rs) == 0:
                            # increment the count of different versions of this format
                            f['version_count'] = int(f['version_count']) + 1
                            f.save()

                            # create the new version entry
                            key = self.create_version_entry(authortitle, fmt, f['version_count'], ebooks[authortitle][fmt]['size'], ebooks[authortitle][fmt]['filehash'])
                        else:
                            print "ignoring exact duplicate %s" % authortitle


    def create_book_entry(self, authortitle, formats):
        key = hashlib.md5(authortitle).hexdigest()
        b = self.bookdb.new_item(authortitle)
        b.add_value("authortitle", authortitle)
        b.add_value("users", self.user.username)
        b.add_value("formats", formats)
        b.add_value("sdbkey", key)
        b.save()
        return key

    def create_format_entry(self, authortitle, fmt):
        key = hashlib.md5(authortitle + fmt).hexdigest()
        f = self.formatdb.new_item(key)
        f.add_value("authortitle", authortitle)
        f.add_value("format", fmt)
        f.add_value("version_count", 1)
        f.add_value("sdbkey", key)
        f.save()
        return key

    def create_version_entry(self, authortitle, fmt, version, size, filehash):
        key = hashlib.md5(authortitle + '-' + str(version) + fmt).hexdigest()
        v = self.versiondb.new_item(key)
        v.add_value("authortitle", authortitle)
        v.add_value("format", fmt)
        v.add_value("user", self.user.username)
        v.add_value("size", size)
        v.add_value("filehash", filehash)
        v.add_value("sdbkey", key)
        v.save()
        return key


    def set_uploaded(self, sdbkey):
        v = self.versiondb.get_item(sdbkey)
        v.add_value("uploaded", True)
        v.save()


    def store_ebook(self, sdbkey, filehash, filepath):
        # connect to S3
        self.s3 = boto.connect_s3(app.config['AWS_ACCESS_KEY'], app.config['AWS_SECRET_KEY'])
        b = self.s3.get_bucket(app.config['S3_BUCKET'])
        k = Key(b)
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
            # push file to S3
            k.set_contents_from_filename(filepath, None, False, None, 10, None, md5_tup)

            # mark ebook as saved
            self.set_uploaded(sdbkey)

        # always delete local file
        os.remove(filepath)


    def verify_ebook(self, sdbkey):
        # TODO @periodic verify
        # load SDB record
        # get file from S3
        # calculate file hash and verify
        # update SDB verify=True or uploaded=False
        # delete file
        pass


    def find_missing_books(self):
        # query for books which have no uploaded file
        return self.sdb.select("ogre_versions", "select sdbkey, filehash from ogre_versions where uploaded is null and user = '%s'" % self.user.username)


    def update_timestamp(self):
        # set library updated timestamp
        meta = bookdb.get_item("meta")
        if meta == None:
            meta = bookdb.new_item("meta")

        meta['updated'] = datetime.utcnow().isoformat()
        meta.save()


