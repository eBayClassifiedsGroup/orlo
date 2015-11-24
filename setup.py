#!/usr/bin/env python

# from distutils.core import setup
from setuptools import setup, find_packages
import multiprocessing  # nopep8

setup(
    name='orlo',
    version='0.0.2',
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
