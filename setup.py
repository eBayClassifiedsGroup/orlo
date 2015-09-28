#!/usr/bin/env python

# from distutils.core import setup
from setuptools import setup, find_packages
import multiprocessing  # nopep8

setup(name='sponge',
      version='0.0.1',
      description='Deployment data capture API',
      author='Alex Forbes',
      author_email='alforbes@ebay.com',
      license='GPL',
      long_description=open('README.md').read(),
      url='https://github.com/eBayClassifiedsGroup/sponge',
      packages=find_packages(),
      include_package_data=True,
      install_requires=[
              'Flask',
              'Flask-SQLAlchemy',
              'Flask-Testing',
              'Flask-Migrate',
              'sqlalchemy-utils',
      ],
      test_suite='tests',
      )
