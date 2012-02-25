from boto.s3.key import Key


class Factory():
    sdb = None
    bookdb = None
    formatdb = None
    versiondb = None
    s3 = None
    bucket = None

    @staticmethod
    def connect_sdb():
        if Factory.sdb is None:
            Factory.sdb = boto.connect_sdb(app.config['AWS_ACCESS_KEY'], app.config['AWS_SECRET_KEY'])

        return Factory.sdb

    @staticmethod
    def connect_bookdb():
        Factory.connect_sdb()

        if Factory.bookdb is None:
            Factory.bookdb = Factory.sdb.get_domain("ogre_books")

        return Factory.bookdb

    @staticmethod
    def connect_formatdb():
        Factory.connect_sdb()

        if Factory.formatdb is None:
            Factory.formatdb = Factory.sdb.get_domain("ogre_formats")

        return Factory.formatdb

    @staticmethod
    def connect_versiondb():
        Factory.connect_sdb()

        if Factory.versiondb is None:
            Factory.versiondb = Factory.sdb.get_domain("ogre_versions")

        return Factory.versiondb

    @staticmethod
    def connect_s3():
        if Factory.s3 is None:
            Factory.s3 = boto.connect_s3(app.config['AWS_ACCESS_KEY'], app.config['AWS_SECRET_KEY'])

        if Factory.bucket is None:
            Factory.bucket = Factory.s3.get_bucket(app.config['S3_BUCKET'])

        return Factory.bucket
    
    @staticmethod
    def get_key(bucket):
        if Factory.s3 is None or bucket is None:
            raise AttributeError

        return Key(bucket)

