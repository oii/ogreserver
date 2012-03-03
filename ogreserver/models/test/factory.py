from ogreserver import db
from hashlib import md5
import base64
from UserDict import DictMixin
from sqlalchemy.exc import IntegrityError

class Factory():
    sdb = None
    bookdb = None
    versiondb = None

    @staticmethod
    def connect_sdb():
        Factory.connect_bookdb()
        return TestBucket()

    @staticmethod
    def connect_bookdb():
        if Factory.bookdb is None:
            Factory.bookdb = TestBookBucket()

        return Factory.bookdb

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
        elif bucket == "ogre_formats":
            return Factory.formatdb.select(bucket, sql)
        elif bucket == "ogre_books":
            return Factory.bookdb.select(bucket, sql)

    def new_item(self, sdbkey):
        return TestItem()

    def get_item(self, sdbkey):
        return None


class TestItem():
    def add_value(self, name, value):
        pass

    def save(self):
        pass


class TestBookBucket():
    def select(self, bucket, sql):
        print sql
        if sql is not None:
            items = db.session.execute(sql)
        else:
            items = TestBook.query.all()

        out = []
        for ti in items:
            users = ti.users.split(",")
            formats = ti.formats.split(",")
            out.append({'sdbkey':ti['sdbkey'], 'authortitle':ti['authortitle'], 'users':users, 'formats':formats})

        return out

    def new_item(self, sdbkey):
        return TestBook(sdbkey)

    def get_item(self, sdbkey):
        return TestBook.query.filter_by(sdbkey=sdbkey).first()


class TestBook(db.Model, DictMixin):
    __tablename__ = 'ogre_books'
    id = db.Column(db.Integer, primary_key=True)
    authortitle = db.Column(db.String(500))
    users = db.Column(db.String(200))
    formats = db.Column(db.String(200))
    sdbkey = db.Column(db.String(256), unique=True)

    def __init__(self, sdbkey):
        self.sdbkey = sdbkey
        self._users = []
        self._formats = []

    def add_value(self, item, value):
        self.__setitem__(item, value)

    def save(self):
        try:
            db.session.add(self)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()

    def __getitem__(self, item):
        if item == "authortitle":
            return self.authortitle

        if item == "users":
            if self.users is not None:
                self._users = self.users.split(',')
                return self._users
            else:
                return []

        if item == "formats":
            if self.formats is not None:
                self._formats = self.formats.split(',')
                return self._formats
            else:
                return []

    def __setitem__(self, item, value):
        if item == "authortitle":
            self.authortitle = value

        if item == "users":
            if type(value) is list:
                self._users = value
            else:
                self._users.append(value)

            self.users = ','.join(self._users)

        if item == "formats":
            if type(value) is list:
                self._formats = value
            else:
                self._formats.append(value)

            self.formats = ','.join(self._formats)

        self.save()

    def __delitem__(self, item):
        pass

    def keys(self):
        pass


class TestFormatBucket():
    def select(self, bucket, sql):
        if sql is not None:
            items = db.session.execute(sql)
        else:
            items = TestFormat.query.all()

        out = []
        for ti in items:
            out.append({'sdbkey':ti.sdbkey, 'authortitle':ti.authortitle, 'format':ti.format})

        return out

    def new_item(self, sdbkey):
        return TestFormat(sdbkey)

    def get_item(self, sdbkey):
        return TestFormat.query.filter_by(sdbkey=sdbkey).first()


class TestFormat(db.Model):
    __tablename__ = 'ogre_formats'
    id = db.Column(db.Integer, primary_key=True)
    authortitle = db.Column(db.String(500))
    format = db.Column(db.String(20))
    version_count = db.Column(db.Integer)
    sdbkey = db.Column(db.String(256))

    def __init__(self, sdbkey):
        self.sdbkey = sdbkey

    def add_value(self, item, value):
        setattr(self, item, value)

    def save(self):
        try:
            db.session.add(self)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()


class TestVersionBucket():
    def select(self, bucket, sql):
        if sql is not None:
            items = db.session.execute(sql)
        else:
            items = TestVersion.query.all()

        out = []
        for ti in items:
            out.append({'filehash':ti.filehash, 'format':ti.format, 'sdbkey':ti.sdbkey})

        return out

    def new_item(self, sdbkey):
        return TestVersion(sdbkey)

    def get_item(self, sdbkey):
        return TestVersion.query.filter_by(sdbkey=sdbkey).first()


class TestVersion(db.Model):
    __tablename__ = 'ogre_versions'
    id = db.Column(db.Integer, primary_key=True)
    authortitle = db.Column(db.String(500))
    version = db.Column(db.Integer)
    format = db.Column(db.String(20))
    user = db.Column(db.String(100))
    size = db.Column(db.Integer)
    filehash = db.Column(db.String(256))
    uploaded = db.Column(db.Boolean)
    dedrm = db.Column(db.Boolean)
    sdbkey = db.Column(db.String(256))

    def __init__(self, sdbkey):
        self.sdbkey = sdbkey

    def add_value(self, item, value):
        setattr(self, item, value)

    def save(self):
        try:
            db.session.add(self)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()


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

