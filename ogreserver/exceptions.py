from __future__ import unicode_literals


class OgreException(Exception):
    def __init__(self, message=None, inner_excp=None):
        super(OgreException, self).__init__(message)
        self.inner_excp = inner_excp

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
