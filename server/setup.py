import json
import os.path

from setuptools import setup


TESTS_REQUIRE = file('test.requirements').read().splitlines()

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
        'Django==1.4.5',
        'django-tastypie==0.9.12',
        'pil==1.1.7',
    ],
    tests_require=TESTS_REQUIRE,
    description="Customer experience management server",
    url="http://github.com/jesteria/omnispective",
)
