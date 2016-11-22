import orlo
import unittest
import os
from flask_testing import TestCase, LiveServerTestCase
from orlo.orm import db
from orlo.orm import Release, db, Package
from orlo.util import append_or_create_platforms

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
        db.engine.dispose()


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
        app.config['LIVESERVER_PORT'] = 8943
        app.config['LIVESERVER_TIMEOUT'] = 5

        return orlo.app

    def setUp(self):
        # db.engine.dispose()
        db.create_all()
        db.session.begin_nested()

    def tearDown(self):
        db.session.rollback()
        db.session.close()
        db.drop_all()  # stall here implies connection leak
        db.session.remove()
        db.get_engine(self.app).dispose()


class ReleaseDbUtil(object):
    """
    Utility functions for creating releases in the database
    """
    @classmethod
    def _create_release(cls,
                        user='testuser',
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

    @classmethod
    def _create_package(cls,
                        release_id,
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

    @classmethod
    def _start_package(cls, package_id):
        """
        Start a package

        :param package_id:
        """
        package = db.session.query(Package).filter(Package.id == package_id).one()
        package.start()
        db.session.commit()

        return package.id

    @classmethod
    def _stop_package(cls, package_id, success=True):
        """
        Stop a package

        :param package_id:
        """
        package = db.session.query(Package).filter(Package.id == package_id).one()
        package.stop(success=success)
        db.session.commit()

    @classmethod
    def _stop_release(cls, release_id):
        """
        Stop a release

        :param release_id:
        """
        release = db.session.query(Release).filter(Release.id == release_id).one()
        release.stop()
        db.session.commit()

    @classmethod
    def _create_finished_release(cls, success=True):
        """
        Create a completed release using internal methods
        """

        release_id = cls._create_release()
        package_id = cls._create_package(release_id)

        cls._start_package(package_id)
        cls._stop_package(package_id, success=success)
        cls._stop_release(release_id)
        db.session.commit()


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
