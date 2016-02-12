#!/usr/bin/env python

# from distutils.core import setup
from setuptools import setup
import multiprocessing  # nopep8


VERSION = '0.1.1-1'
version_file = open('./orlo/_version.py', 'w')
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
    ],
    test_suite='tests',
)
