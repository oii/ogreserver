from . import OgreError


class AuthDeniedError(OgreError):
    pass

class AuthError(OgreError):
    pass

class NoEbooksError(OgreError):
    pass

class NoUploadsError(OgreError):
    pass

class BaconError(OgreError):
    pass

class MushroomError(OgreError):
    pass

class SpinachError(OgreError):
    pass

class CorruptEbookError(OgreError):
    pass
