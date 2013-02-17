import json
import os.path

_CWD = os.path.dirname(os.path.abspath(__file__))

VERSION = json.load(file(os.path.join(_CWD, 'version.json')))

__version__ = VERSION['version']
__version_number__ = VERSION['versionNumber']
