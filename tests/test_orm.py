from __future__ import print_function
from tests.test_contract import OrloTest
from random import randrange
from orlo.orm import db
from orlo.orm import Release, Package, PackageResult, Platform
from orlo import app
from orlo.util import append_or_create_platforms
from sqlalchemy.orm import exc
import arrow
import datetime
import uuid

__author__ = 'alforbes'

'''
Tests for the database / orm layer
'''


class OrloDbTest(OrloTest):
    """
    Base test class for tests that need to manipulate data without using the http API
    """

    def _create_release(self,
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

    @staticmethod
    def _start_package(package_id):
        """
        Start a package

        :param package_id:
        """
        package = db.session.query(Package).filter(Package.id == package_id).one()
        package.start()
        db.session.commit()

        return package.id

    @staticmethod
    def _stop_package(package_id, success=True):
        """
        Stop a package

        :param package_id:
        """
        package = db.session.query(Package).filter(Package.id == package_id).one()
        package.stop(success=success)
        db.session.commit()

    @staticmethod
    def _stop_release(release_id):
        """
        Stop a release

        :param release_id:
        """
        release = db.session.query(Release).filter(Release.id == release_id).one()
        release.stop()
        db.session.commit()

    def _create_finished_release(self, success=True):
        """
        Create a completed release using internal methods
        """

        release_id = self._create_release()
        package_id = self._create_package(release_id)

        self._start_package(package_id)
        self._stop_package(package_id, success=success)
        self._stop_release(release_id)
        db.session.commit()


class TestFields(OrloDbTest):
    def setUp(self):
        super(OrloDbTest, self).setUp()

        for r in range(0, 3):
            self._create_finished_release()

    def test_release_types(self):
        """
        Test the types returned by Release objects are OK
        """
        r = db.session.query(Release).first()
        self.assertIs(type(r.id), uuid.UUID)
        self.assertIs(hasattr(r.notes, '__iter__'), True)
        self.assertIs(hasattr(r.platforms, '__iter__'), True)
        self.assertIs(type(r.references), unicode)
        self.assertIs(type(list(r.references)), list)
        self.assertIs(type(r.stime), arrow.arrow.Arrow)
        self.assertIs(type(r.ftime), arrow.arrow.Arrow)
        self.assertIs(type(r.duration), datetime.timedelta)
        self.assertIs(type(r.team), unicode)

    def test_package_types(self):
        """
        Test the types returned by Package objects are OK
        """
        p = db.session.query(Package).first()
        x = db.session.query(Package).all()
        self.assertIs(type(p.id), uuid.UUID)
        self.assertIs(type(p.name), unicode)
        self.assertIs(type(p.stime), arrow.arrow.Arrow)
        self.assertIs(type(p.ftime), arrow.arrow.Arrow)
        self.assertIs(type(p.duration), datetime.timedelta)
        self.assertIs(type(p.status), unicode)
        self.assertIs(type(p.version), unicode)
