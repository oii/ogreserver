class OgreException(Exception):
    pass

class ConfigSetupError(OgreException):
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

class FailedDebugLogsError(OgreException):
    pass

class KindlePrereqsError(OgreException):
    pass

class NoEbookSourcesFoundError(OgreException):
    pass
