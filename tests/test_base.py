import orlo
import unittest
import os
from flask_testing import TestCase, LiveServerTestCase
from orlo.util import append_or_create_platforms
from orlo.orm import db, Release, Package

try:
    TRAVIS = True if os.environ['TRAVIS'] == 'true' else False
except KeyError:
    TRAVIS = False


class OrloTest(TestCase):
    """
    Base test class to setup the app
    """
    def create_app(self):
        if TRAVIS:
            db_uri = 'postgres://orlo:password@localhost:5432/orlo'
        else:
            db_uri = 'postgres://orlo:password@192.168.57.100:5432/orlo'
        app = orlo.app
        app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
        # app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
        app.config['TESTING'] = True
        app.config['DEBUG'] = False
        app.config['TRAP_HTTP_EXCEPTIONS'] = True
        app.config['PRESERVE_CONTEXT_ON_EXCEPTION'] = False

        return orlo.app

    def setUp(self):
        db.create_all()
        db.session.begin_nested()

    def tearDown(self):
        db.session.rollback()
        db.session.remove()
        db.drop_all()


class OrloLiveTest(LiveServerTestCase):
    """
    Test on a live server
    """

    def create_app(self):
        if TRAVIS:
            db_uri = 'postgres://orlo:password@localhost:5432/orlo'
        else:
            db_uri = 'postgres://orlo:password@192.168.57.100:5432/orlo'

        app = orlo.app
        app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
        # app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
        app.config['TESTING'] = True
        app.config['DEBUG'] = False
        app.config['TRAP_HTTP_EXCEPTIONS'] = True
        app.config['PRESERVE_CONTEXT_ON_EXCEPTION'] = False

        return orlo.app

    def setUp(self):
        db.create_all()
        db.session.begin_nested()

    def tearDown(self):
        db.session.rollback()
        db.drop_all()
        db.session.remove()
        db.get_engine(self.app).dispose()


class LiveDbTest(OrloLiveTest):
    def setUp(self):
        # super(DeployTest, self).setUp()
        db.create_all()

    @staticmethod
    def _create_release(user='testuser',
                        team='test team',
                        platforms=None,
                        references=None,
                        success=True):
        """
        Create a release using internal methods

        :param user:
        :param team:
        :param platforms:
        :param references:
        :return:
        """

        if not platforms:
            platforms = ['test_platform']
        if type(platforms) is not list:
            raise AssertionError("Platforms parameter must be list")
        if not references:
            references = ['TestTicket-123']

        db_platforms = append_or_create_platforms(platforms)

        r = Release(
            platforms=db_platforms,
            user=user,
            references=references,
            team=team,
        )
        db.session.add(r)
        db.session.commit()

        return r.id

    @staticmethod
    def _create_package(release_id,
                        name='test-package',
                        version='1.2.3',
                        diff_url=None,
                        rollback=False,
                        ):
        """
        Create a package using internal methods

        :param release_id:
        :param name:
        :param version:
        :param diff_url:
        :param rollback:
        :return:
        """
        p = Package(
            release_id=release_id,
            name=name,
            version=version,
            diff_url=diff_url,
            rollback=rollback,
        )
        db.session.add(p)
        db.session.commit()

        return p.id


class ConfigChange(object):
    def __init__(self, section, option, value):
        """
        Decorator to temporarily change configuration

        @param section: ConfigParser section
        @param option: ConfigParser option
        @param value: Value to set
        @return:
        """
        self.section = section
        self.option = option
        self.value = value

    def __enter__(self):
        self.original_state = orlo.config.get(self.section, self.option)
        orlo.config.set(self.section, self.option, self.value)

    def __exit__(self, exc_type, exc_val, exc_tb):
        orlo.config.set(self.section, self.option, self.original_state)
