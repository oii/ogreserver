from ogreserver import app, celery, boto

from ogreserver.models.user import User
from ogreserver.models.datastore import DataStore
from ogreserver.models.reputation import Reputation


@celery.task(name="ogreserver.store_ebook")
def store_ebook(user_id, sdbkey, filehash, fmt):
    user = User.query.get(user_id)

    filepath = "%s/%s%s" % (app.config['UPLOADED_EBOOKS_DEST'], filehash, fmt)

    print "store_ebook: %s %s%s" % (sdbkey, filehash, fmt)

    # store the file into S3
    ds = DataStore(user)
    ds.store_ebook(sdbkey, filehash, filepath)

    # handle badge and reputation changes
    r = Reputation(user)
    r.earn_badges()

