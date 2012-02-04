from ogreserver import app, celery, boto

from ogreserver.models.datastore import DataStore


@celery.task(name="ogreserver.store_ebook")
def store_ebook(sdbkey, filehash):
    filepath = "%s/%s" % (app.config['UPLOADED_EBOOKS_DEST'], filehash)

    # store the file into S3
    ds = DataStore(None)
    print "store_ebook: %s %s" % (sdbkey, filehash)
    ds.store_ebook(sdbkey, filehash, filepath)


# TODO @periodic verify

