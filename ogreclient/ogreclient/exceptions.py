class OgreException(Exception):
    pass

class AuthDeniedError(OgreException):
    pass

class AuthError(OgreException):
    pass

class NoEbooksError(OgreException):
    pass

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
