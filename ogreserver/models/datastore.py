import datetime
import hashlib
import json
import re

import boto
from boto.exception import S3ResponseError

from ogreserver import app
from ogreserver.models.factory import Factory


class DataStore():

    def __init__(self, user):
        self.user = user

    def list(self, next_token=None):
        sdb = Factory.connect_sdb()
        return sdb.select("ogre_books", "select authortitle, sdb_key, users, formats from ogre_books", next_token=next_token)

    def search(self, s):
        sdb = Factory.connect_sdb()
        return sdb.select("ogre_books", "select authortitle, sdb_key, users, formats from ogre_books where searchtext like '%%%s%%'" % s)

    def update_library(self, ebooks):
        new_ebook_count = 0
        sdb = boto.connect_sdb(app.config['AWS_ACCESS_KEY'], app.config['AWS_SECRET_KEY'])
        domain = sdb.get_domain("ogre_ebooks")

        for authortitle in ebooks.keys():
            #try:
            # first check if this exact file has been uploaded before
            found_duplicate = False

            if DataStore.check_ebook_exists(ebooks[authortitle]['filemd5']) == True:
                found_duplicate = True
                # TODO any way we can import meta data from this book?
                break

            if found_duplicate == True:
                print "ignoring exact duplicate %s" % authortitle
                continue

            # check for this book by meta data in the library
            bkey = DataStore.build_ebook_key(authortitle)
            b = domain.get_item(bkey)

            if b is None:
                # create this as a new book
                ebook = {
                    'authortitle': authortitle,
                    'formats': ebooks[authortitle]['format'],
                    'versions': {},
                }
                # add the first version
                ebook['versions']['1'] = self.create_ebook_version_object(1,
                    ebooks[authortitle]['size'],
                    ebooks[authortitle]['format'],
                    ebooks[authortitle]['filemd5']
                )
                new_ebook_count += 1

                self.create_ebook(ebook, self.user.username, ebooks[authortitle]['filemd5'])
            else:
                # parse the ebook data
                ebook_data = json.loads(b['data'])
                print json.dumps(ebook_data, indent=4)

                # reject if this user has uploaded another version of this book before
                for version_id in ebook_data['versions']:
                    if ebook_data['versions'][version_id]['user'] == self.user.username:
                        print "rejecting alternate format of existing book"
                        continue

                # calculate the next highest version number
                version_nums = [int(n) for n in ebook_data['versions'].keys()]
                next_version = max(version_nums) + 1

                # TODO favour mobi format in uploads.. epub after that - dont upload multiple formats of same book
                # test user upload of a mobi, then same user tries to upload epub version
                # then user could upload a re-mobi of that book - which becomes a new version

                # add another version of this ebook
                ebook_data['versions'][next_version] = self.create_ebook_version_object(
                    next_version,
                    ebooks[authortitle]['size'],
                    ebooks[authortitle]['format'],
                    ebooks[authortitle]['filemd5']
                )
                print ebook_data

                new_ebook_count += 1

                # add user to set of owners
                if self.user.username not in b['users']:
                    b.add_value("users", self.user.username)

                # TODO version popularity determines which formats appear on ebook base top-level
                # popularity += 1 for download
                # popularity += 5 for quality review
                # use quality as co-efficient when calculating most popular

                # append to the set of this book's formats
                if ebooks[authortitle]['format'] not in b['formats']:
                    b.add_value("formats", ebooks[authortitle]['format'])

                # write book into SDB
                b['data'] = json.dumps(ebook_data)
                b.save()

            #except Exception as e:
            #    print "[EXCP] %s" % authortitle
            #    print "\t%s: %s" % (type(e), e)

        return new_ebook_count

    def create_ebook_version_object(self, num, size, fmt, filemd5):
        return {
            'version': num,
            'user': self.user.username,
            'size': size,
            'popularity': 1,
            'quality': 0.5,
            'rating': None,
            'original_format': fmt,
            'formats': {
                fmt: {
                    'filemd5': filemd5,
                    'uploaded': 0,
                }
            }
        }

    def create_ebook(self, data, creator, hashes):
        sdb = boto.connect_sdb(app.config['AWS_ACCESS_KEY'], app.config['AWS_SECRET_KEY'])
        domain = sdb.get_domain("ogre_ebooks")

        key = DataStore.build_ebook_key(data['authortitle'])
        obj = domain.new_item(key)

        obj['data'] = json.dumps(data)
        obj['users'] = creator
        obj['searchtext'] = data['authortitle'].encode("UTF-8").lower()
        obj['hashes'] = hashes
        obj['all_uploaded'] = "false"
        obj['sdb_key'] = key
        obj.save()
        return key

    @staticmethod
    def get_version_count(sdb_key):
        sdb = Factory.connect_sdb()
        rs = sdb.select("ogre_ebooks", "select itemName() from ogre_ebooks where itemName() = '%s'" % sdb_key)
        return len(rs)

    @staticmethod
    def check_ebook_exists(filemd5):
        sdb = Factory.connect_sdb()
        rs = sdb.select("ogre_ebooks", "select itemName() from ogre_ebooks where hashes = '%s'" % filemd5)
        return (len(rs) > 0)

    @staticmethod
    def build_ebook_key(authortitle):
        return hashlib.md5((authortitle).encode("UTF-8")).hexdigest()

    @staticmethod
    def get_ebook_url(sdb_key, fmt):
        sdb = boto.connect_sdb(app.config['AWS_ACCESS_KEY'], app.config['AWS_SECRET_KEY'])
        domain = sdb.get_domain("ogre_ebooks")
        b = domain.get_item(sdb_key)
        if b is None:
            raise Exception("Unknown key %s" % sdb_key)

        ebook_data = json.loads(b['data'])
        return DataStore.generate_filename(ebook_data['authortitle'], ebook_data['formats'][fmt]['filemd5'], fmt)

    @staticmethod
    def set_uploaded(sdb_key, version, fmt, isit=True):
        sdb = boto.connect_sdb(app.config['AWS_ACCESS_KEY'], app.config['AWS_SECRET_KEY'])
        domain = sdb.get_domain("ogre_ebooks")
        b = domain.get_item(sdb_key)
        if b is None:
            raise Exception("Unknown key %s" % sdb_key)

        ebook_data = json.loads(b['data'])
        if isit == False:
            ebook_data['versions'][version]['formats'][fmt]['uploaded'] = False
        else:
            ebook_data['versions'][version]['formats'][fmt]['uploaded'] = True

        b['data'] = json.dumps(ebook_data)
        b.save()

    @staticmethod
    def set_dedrm_flag(sdb_key, fmt):
        sdb = boto.connect_sdb(app.config['AWS_ACCESS_KEY'], app.config['AWS_SECRET_KEY'])
        domain = sdb.get_domain("ogre_ebooks")
        b = domain.get_item(sdb_key)
        if b is None:
            raise Exception("Unknown key %s" % sdb_key)

        ebook_data = json.loads(b['data'])
        ebook_data['formats']['fmt']['dedrm'] = None
        b['data'] = json.dumps(ebook_data)
        b.save()

    @staticmethod
    def store_ebook(sdb_key, filemd5, filename, filepath, version, fmt):
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
                DataStore.set_uploaded(sdb_key, version, fmt)

            except S3ResponseError:
                # TODO log
                raise S3DatastoreError("Upload failed checksum 2")

    @staticmethod
    def generate_filename(authortitle, filemd5, fmt):
        # TODO transpose unicode
        return "%s.%s.%s" % (re.sub("[^a-zA-Z0-9]", "_", authortitle), filemd5[0:6], fmt)

    @staticmethod
    def get_missing_books(username=None, verify_s3=False):
        sdb = boto.connect_sdb(app.config['AWS_ACCESS_KEY'], app.config['AWS_SECRET_KEY'])

        if username is not None:
            if verify_s3 == True:
                rs = sdb.select("ogre_ebooks", "select sdb_key, data from ogre_ebooks where users = '%s'" % username)
            else:
                rs = sdb.select("ogre_ebooks", "select sdb_key, data from ogre_ebooks where all_uploaded = 'false' and users = '%s'" % username)
        else:
            if verify_s3 == True:
                raise Exception("Can't verify entire library in one go.")
            else:
                rs = sdb.select("ogre_ebooks", "select sdb_key, data from ogre_ebooks where all_uploaded = 'false'")

        output = []

        # flatten for output
        for ebook in rs:
            ebook_data = json.loads(ebook['data'])
            for v in ebook_data['versions']:
                version = ebook_data['versions'][v]
                for fmt in version['formats']:
                    output.append({
                        'sdb_key': ebook['sdb_key'],
                        'authortitle': ebook_data['authortitle'],
                        'filemd5': version['formats'][fmt]['filemd5'], 
                        'version': v,
                        'format': fmt,
                    })

        if verify_s3 == True:
            # verify books are on S3
            bucket = Factory.connect_s3()
            for b in output:
                filename = DataStore.generate_filename(b['authortitle'], b['filemd5'], b['format'])
                k = Factory.get_key(bucket, filename)
                DataStore.set_uploaded(b['sdb_key'], b['version'], b['format'], k.exists())
                # TODO update rs when verify=True

        return output

    @staticmethod
    def update_timestamp():
        sdb = boto.connect_sdb(app.config['AWS_ACCESS_KEY'], app.config['AWS_SECRET_KEY'])
        domain = sdb.get_domain("ogre_ebooks")

        # set library updated timestamp
        meta = domain.get_item("meta")
        if meta == None:
            meta = domain.new_item("meta")

        meta['updated'] = datetime.datetime.utcnow().isoformat()
        meta.save()


class S3DatastoreError(Exception):
    pass