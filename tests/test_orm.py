from __future__ import print_function
from tests.test_contract import OrloTest
from random import randrange
from tests.test_contract import db
from orlo.orm import Release, Package, PackageResult, Platform
import arrow
import datetime
import uuid

__author__ = 'alforbes'

'''
Tests for the database / orm layer
'''


class OrloDbTest(OrloTest):
    def setUp(self):
        super(OrloDbTest, self).setUp()

        # Setup a platform
        self.platform = Platform('TEST-PLATFORM')

        # Add 10 releases
        for i in range(10):
            self._add_release(i)

    def _add_release(self, i):
        r = Release(
            platforms=[self.platform],
            user='TEST USER',
            references=['REF-{}'.format(randrange(99, 1000)) * 2],
            team='TEST TEAM',
        )
        db.session.add(r)

        r.start()
        for _ in range(0, 2):
            self._add_package(r.id)
        r.stop()
        db.session.commit()

    def _add_package(self, release_id):
        """
        Add a package to a release
        """
        p = Package(
            release_id=release_id,
            name='TestPackage-{}'.format(randrange(0, 10)),
            version=str(randrange(0, 1000)),
        )
        db.session.add(p)
        p.start()
        p.stop(success=True)

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
        self.assertIs(type(p.id), uuid.UUID)
        self.assertIs(type(p.name), unicode)
        self.assertIs(type(p.stime), arrow.arrow.Arrow)
        self.assertIs(type(p.ftime), arrow.arrow.Arrow)
        self.assertIs(type(p.duration), datetime.timedelta)
        self.assertIs(type(p.status), unicode)
        self.assertIs(type(p.version), unicode)
