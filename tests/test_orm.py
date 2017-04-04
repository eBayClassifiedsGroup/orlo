from __future__ import print_function
from test_route_base import OrloTest
from random import randrange
from orlo.orm import db
from orlo.orm import Release, Package, PackageResult, Platform
from orlo.app import app
from sqlalchemy.orm import exc
import arrow
import datetime
import uuid
from six import string_types
from test_base import ReleaseDbUtil

__author__ = 'alforbes'

'''
Tests for the database / orm layer
'''


class OrloDbTest(OrloTest, ReleaseDbUtil):
    """
    Base test class for tests that need to manipulate data without using the http API
    """


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
        self.assertIsInstance(r.id, uuid.UUID)
        self.assertIs(hasattr(r.notes, '__iter__'), True)
        self.assertIs(hasattr(r.platforms, '__iter__'), True)
        self.assertIsInstance(r.references, string_types)
        self.assertIs(type(list(r.references)), list)
        self.assertIsInstance(r.stime, arrow.arrow.Arrow)
        self.assertIsInstance(r.ftime, arrow.arrow.Arrow)
        self.assertIsInstance(r.duration, datetime.timedelta)
        self.assertIsInstance(r.team, string_types)

    def test_package_types(self):
        """
        Test the types returned by Package objects are OK
        """
        p = db.session.query(Package).first()
        x = db.session.query(Package).all()
        self.assertIsInstance(p.id, uuid.UUID)
        self.assertIsInstance(p.name, string_types)
        self.assertIsInstance(p.stime, arrow.arrow.Arrow)
        self.assertIsInstance(p.ftime, arrow.arrow.Arrow)
        self.assertIsInstance(p.duration, datetime.timedelta)
        self.assertIsInstance(p.status, string_types)
        self.assertIsInstance(p.version, string_types)
