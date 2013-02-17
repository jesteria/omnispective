import json
import os.path

from setuptools import setup


VERSION = json.load(file(os.path.join('omniclient', 'version.json')))

setup(
    name="omnispective-client",
    packages=['omniclient'],
    version=VERSION['version'],
    install_requires=[
        'requests==1.1.0',
    ],
    tests_require=[
        'django-nose>=1.1',
        'mock>=1.0.1',
    ],
    description="Clients for the Omnispective customer experience "
                "management server",
    url="http://github.com/jesteria/omnispective",
)
