#!/usr/bin/env python

# from distutils.core import setup
from setuptools import setup, find_packages
import multiprocessing  # nopep8
import os


__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

VERSION = '0.4.0'

version_file = open(os.path.join(__location__, 'orlo', '_version.py'), 'w')
version_file.write("__version__ = '{}'".format(VERSION))
version_file.close()

tests_require = [
    'Flask-Testing',
    'orloclient>=0.2.0',
    'mockldap',
    'pytest',
    'tox',
]


setup(
    name='orlo',
    version=VERSION,
    description='Deployment data capture API',
    author='Alex Forbes',
    author_email='alforbes@ebay.com',
    license='GPL',
    long_description=open(os.path.join(__location__, 'README.md')).read(),
    url='https://github.com/eBayClassifiedsGroup/orlo',
    packages=find_packages(
        exclude=['tests', 'debian', 'docs', 'etc']
    ),
    include_package_data=True,
    install_requires=[
        'Flask',
        'Flask-Alembic >= 2.0.1',
        'Flask-HTTPAuth',
        'Flask-Migrate',
        'Flask-SQLAlchemy',
        'Flask-Script >= 2.0.5',
        'Flask-TokenAuth',
        'arrow',
        'gunicorn',
        'orloclient>=0.2.0',
        'psycopg2',
        'pyldap',
        'pytz',
        'sphinxcontrib-httpdomain',
        'sqlalchemy-utils',
    ],
    extras_require={
        'test': tests_require,
    },
    tests_require=tests_require,
    test_suite='tests',
    # Creates a script in /usr/local/bin
    entry_points={
        'console_scripts': ['orlo=orlo.__main__:main']
    }
)
