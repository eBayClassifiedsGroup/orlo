#!/usr/bin/env python

# from distutils.core import setup
from setuptools import setup
import multiprocessing  # nopep8
import os


VERSION = '0.2.0-pre1'
my_path = os.path.dirname(os.path.realpath(__file__))
version_file = open('{}/orlo/_version.py'.format(my_path), 'w')
version_file.write("__version__ = '{}'".format(VERSION))
version_file.close()


setup(
    name='orlo',
    version=VERSION,
    description='Deployment data capture API',
    author='Alex Forbes',
    author_email='alforbes@ebay.com',
    license='GPL',
    long_description=open('README.md').read(),
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
