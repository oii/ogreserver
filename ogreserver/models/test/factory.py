from ogreserver import db
from hashlib import md5
import base64

class Factory():
    sdb = None
    versiondb = None

    @staticmethod
    def connect_sdb():
        return TestBucket()

    @staticmethod
    def connect_bookdb():
        return TestBucket()

    @staticmethod
    def connect_formatdb():
        return TestBucket()

    @staticmethod
    def connect_versiondb():
        if Factory.versiondb is None:
            Factory.versiondb = TestVersionBucket()

        return Factory.versiondb

    @staticmethod
    def connect_s3():
        if Factory.versiondb is None:
            Factory.versiondb = TestVersionBucket()

        return Factory.versiondb

    @staticmethod
    def get_key(bucket):
        return TestKey(Factory.versiondb)


class TestBucket():
    def select(self, bucket, sql):
        if bucket == "ogre_versions":
            return Factory.versiondb.select(bucket, sql)

    def new_item(self, sdbkey):
        return TestItem()

    def get_item(self, sdbkey):
        return None


class TestItem():
    def add_value(self, name, value):
        pass

    def save(self):
        pass


class TestVersionBucket():
    def select(self, bucket, sql):
        out = []
        items = TestVersion.query.all()
        for ti in items:
            out.append({'sdbkey':ti.sdbkey, 'filehash':ti.filehash, 'format':ti.format})

        return out

    def new_item(self, sdbkey):
        return TestVersion(sdbkey)

    def get_item(self, sdbkey):
        return TestVersion(sdbkey)


class TestVersion(db.Model):
    __tablename__ = 'testsdb'
    id = db.Column(db.Integer, primary_key=True)
    sdbkey = db.Column(db.String(256))
    filehash = db.Column(db.String(256))
    format = db.Column(db.String(20))

    def __init__(self, sdbkey):
        self.sdbkey = sdbkey
        self.filehash = None

    def add_value(self, name, value):
        if name is "filehash":
            self.filehash = value

        if name is "format":
            self.format = value

    def save(self):
        db.session.add(self)
        db.session.commit()


class TestKey():
    sdb = None
    key = None

    def __init__(self, sdb):
        self.sdb = sdb

    def compute_md5(self, f):
        items = self.sdb.select(None, None)
        for ti in items:
            if ti['sdbkey'] == self.key:
                return (ti['filehash'],)

    def set_contents_from_filename(self, filepath, a, b, c, d, e, md5_tup):
        pass

    def seek(self, a):
        return None

    def read(self, a):
        return None

    def tell(self):
        return None
