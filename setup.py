#!/usr/bin/env python

# from distutils.core import setup
from setuptools import setup
import multiprocessing  # nopep8
import os


__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

VERSION = '0.2.0'

version_file = open(os.path.join(__location__, 'orlo', '_version.py'), 'w')
version_file.write("__version__ = '{}'".format(VERSION))
version_file.close()


setup(
    name='orlo',
    version=VERSION,
    description='Deployment data capture API',
    author='Alex Forbes',
    author_email='alforbes@ebay.com',
    license='GPL',
    long_description=open(os.path.join(__location__, 'README.md')).read(),
    url='https://github.com/eBayClassifiedsGroup/orlo',
    packages=[
        'orlo',
    ],
    include_package_data=True,
    install_requires=[
        'Flask',
        'Flask-Migrate',
        'Flask-SQLAlchemy',
        'Flask-HTTPAuth',
        'Flask-TokenAuth',
        'arrow',
        'gunicorn',
        'psycopg2',
        'pyldap',
        'pytz',
        'sphinxcontrib-httpdomain',
        'sqlalchemy-utils',
    ],
    tests_require=[
        'Flask-Testing',
        'orloclient>=0.1.1',
    ],
    test_suite='tests',
    # Creates a script in /usr/local/bin
    entry_points={
        'console_scripts': ['orlo=orlo.cli:main']
    }
)
