import json
import os.path

_CWD = os.path.dirname(os.path.abspath(__file__))

VERSION = json.load(file(os.path.join(_CWD, 'version.json')))

__version__ = VERSION['version']
__version_number__ = VERSION['versionNumber']


class Defaults(object):

    HOST_IS_SECURE = True


class OmniclientError(Exception):
    pass

class ConfigurationError(OmniclientError):
    pass
