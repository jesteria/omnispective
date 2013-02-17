import json
import os.path

from setuptools import setup


VERSION = json.load(file(os.path.join(
    'omniserver',
    'omniserver',
    'version.json',
)))

setup(
    name="omnispective-server",
    packages=['omniserver'],
    version=VERSION['version'],
    install_requires=[
        'Django==1.4.3',
        'django-tastypie==0.9.12',
    ],
    tests_require=[
        'django-nose>=1.1',
    ],
    description="Customer experience management server",
    url="http://github.com/jesteria/omnispective",
)
