from boto.s3.key import Key as BotoKey
from hashlib import md5
import base64


class Factory():
    sdb = None
    versiondb = None

    @staticmethod
    def connect_sdb():
        return Factory.create_testsdb()

    @staticmethod
    def connect_bookdb():
        return TestSDB()

    @staticmethod
    def connect_formatdb():
        return TestSDB()

    @staticmethod
    def connect_versiondb():
        return Factory.create_testsdb()

    @staticmethod
    def connect_s3():
        return TestSDB()

    @staticmethod
    def create_testsdb():
        if Factory.sdb is None:
            Factory.sdb = TestSDB()

        return Factory.sdb

    @staticmethod
    def get_key(bucket):
        return TestKey()


class TestSDB():
    def __init__(self):
        self.items = []

    def select(self, bucket, sql):
        out = []
        for i in self.items:
            out.append({'sdbkey':i.sdbkey, 'filehash':i.filehash})

        return out

    def new_item(self, sdbkey):
        ti = TestItem(sdbkey)
        self.items.append(ti)
        return ti

    def get_item(self, sdbkey):
        return None


class TestItem():
    def __init__(self, sdbkey):
        self.sdbkey = sdbkey
        self.filehash = None

    def add_value(self, name, value):
        if name is "filehash":
            self.filehash = value

    def save(self):
        pass


class TestKey():
    def compute_md5(self, f):
        return self._compute_md5(f)

    def _compute_md5(fp, buf_size=8192):
        m = md5()
        fp.seek(0)
        s = fp.read(buf_size)
        while s:
            m.update(s)
            s = fp.read(buf_size)

        hex_md5 = m.hexdigest()
        base64md5 = base64.encodestring(m.digest())

        if base64md5[-1] == '\n':
            base64md5 = base64md5[0:-1]

        file_size = fp.tell()
        fp.seek(0)
        return (hex_md5, base64md5, file_size)

