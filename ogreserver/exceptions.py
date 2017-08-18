from __future__ import unicode_literals


class OgreException(Exception):
    def __init__(self, message=None, inner_excp=None):
        super(OgreException, self).__init__(message)
        self.inner_excp = inner_excp

    def __unicode__(self):
        return u'{} ({})'.format(self.message, self.inner_excp)

    def __str__(self):
        return unicode(self).encode('utf8')


class DuplicateBaseError(Exception):
    def __init__(self, ebook_id, file_hash):
        super(DuplicateBaseError, self).__init__()
        self.ebook_id = ebook_id
        self.file_hash = file_hash

class FileHashDuplicateError(DuplicateBaseError):
    def __init__(self, ebook_id, file_hash):
        super(FileHashDuplicateError, self).__init__(ebook_id, file_hash)

class AuthortitleDuplicateError(DuplicateBaseError):
    def __init__(self, ebook_id, file_hash):
        super(AuthortitleDuplicateError, self).__init__(ebook_id, file_hash)

class AsinDuplicateError(DuplicateBaseError):
    def __init__(self, ebook_id):
        super(AsinDuplicateError, self).__init__(ebook_id, None)

class IsbnDuplicateError(DuplicateBaseError):
    def __init__(self, ebook_id):
        super(IsbnDuplicateError, self).__init__(ebook_id, None)

class BadMetaDataError(OgreException):
    pass

class NoFormatAvailableError(OgreException):
    pass

class ConversionFailedError(OgreException):
    pass

class EbookNotFoundOnS3Error(OgreException):
    pass

class SameHashSuppliedOnUpdateError(OgreException):
    pass

class RethinkdbError(OgreException):
    pass

class S3DatastoreError(OgreException):
    pass

class NoMoreResultsError(OgreException):
    pass


class APIBaseError(OgreException):
    pass

class APIAccessDenied(APIBaseError):
    pass

class AmazonAPIError(APIBaseError):
    pass

class AmazonItemNotAccessibleError(AmazonAPIError):
    pass

class AmazonNoMatchesError(AmazonAPIError):
    pass

class AmazonHttpError(AmazonAPIError):
    pass

class GoodreadsAPIError(APIBaseError):
    pass

class GoodreadsBookNotFoundError(OgreException):
    pass

class GoogleAPIError(APIBaseError):
    pass

class GoogleHttpError(GoogleAPIError):
    pass

class GoogleNoMatchesError(GoogleAPIError):
    pass
