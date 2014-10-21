class OgreException(Exception):
    def __init__(self, message=None, inner_excp=None):
        super(OgreException, self).__init__(message)
        self.inner_excp = inner_excp

class ConfigSetupError(OgreException):
    pass

class AuthDeniedError(OgreException):
    pass

class AuthError(OgreException):
    pass

class NoEbooksError(OgreException):
    def __init__(self):
        super(NoEbooksError, self).__init__(u'No ebooks found!')

class NoUploadsError(OgreException):
    pass

class BaconError(OgreException):
    pass

class MushroomError(OgreException):
    pass

class SpinachError(OgreException):
    pass

class CorruptEbookError(OgreException):
    pass

class FailedWritingMetaDataError(OgreException):
    pass

class FailedConfirmError(OgreException):
    pass

class FailedDebugLogsError(OgreException):
    pass

class KindlePrereqsError(OgreException):
    pass

class NoEbookSourcesFoundError(OgreException):
    pass

class DuplicateEbookFoundError(OgreException):
    pass

class MissingFromCacheError(OgreException):
    pass
