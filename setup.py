#!/usr/bin/env python

import sys

from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand

class PyTest(TestCommand):
    def initialize_options(self):
        TestCommand.initialize_options(self)

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest
        errno = pytest.main(['tests'])
        sys.exit(errno)

setup(
    name='Flask-RESTful',
    version='0.3.0',
    url='https://www.github.com/flask-restful/flask-restful/',
    author='Twilio API Team',
    author_email='help@twilio.com',
    description='Simple framework for creating REST APIs',
    packages=find_packages(exclude=['tests']),
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    cmdclass = {'test': PyTest},
    install_requires=[
        'aniso8601>=0.82',
        'Flask>=0.8',
        'six>=1.3.0',
        'pytz',
    ],
    tests_require=[
        'Flask-RESTful[paging]',
        'mock>=0.8',
        'pytest'
    ],
    # Install these with "pip install -e '.[paging]'" or '.[docs]'
    extras_require={
        'paging': 'pycrypto>=2.6',
        'docs': 'sphinx',
    }
)
