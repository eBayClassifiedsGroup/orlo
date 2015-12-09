from __future__ import print_function, unicode_literals
import json
from orlo.orm import Release, Package, db
from orlo.config import config
from orlo.util import string_to_list
from tests.test_contract import OrloTest

__author__ = 'alforbes'


class ImportTest(OrloTest):
    doc = {
        'platforms': ['test_platform'],
        'ftime': '2015-11-18T19:21:12Z',
        'stime': '2015-11-18T19:21:12Z',
        'team': 'test team',
        'references': ['TestTicket-123'],
        'packages': [
            {
                'status': 'SUCCESSFUL',
                'name': 'test-package',
                'version': '1.2.3',
                'ftime': '2015-11-18T19:21:12Z',
                'stime': '2015-11-18T19:21:12Z',
                'diff_url': None,
                'rollback': False,
            }
        ],
        'user': 'testuser'
    }

    def setUp(self):
        db.create_all()
        self._import_doc()

    def test_get_import(self):
        """
        Test that GET /import returns 200
        """
        response = self.client.get('/import')
        self.assert200(response)

    def _import_doc(self):
        """
        Import our test document
        """

        response = self.client.post(
            '/import/release',
            data=json.dumps(self.doc),
            content_type='application/json',
        )

        self.assert200(response)
        self.release = db.session.query(Release).first()
        self.package = db.session.query(Package).first()

    def test_import_param_platforms(self):
        """
        Test that the platforms field is imported successfully
        """
        self.assertEqual(self.release.platforms, unicode(self.doc['platforms']))

    def test_import_param_ftime(self):
        """
        Test finish time matches
        """

        self.assertEqual(
            self.release.ftime.strftime(config.get('main', 'time_format')),
            self.doc['stime'])

    def test_import_param_stime(self):
        """
        Test start time matches
        """
        self.assertEqual(
            self.release.stime.strftime(config.get('main', 'time_format')),
            self.doc['stime'])

    def test_import_param_team(self):
        """
        Test imported team matches
        """
        self.assertEqual(self.release.team, self.doc['team'])

    def test_import_param_references(self):
        """
        Test imported references match
        """
        self.assertEqual(self.release.references, unicode(self.doc['references']))

    def test_import_param_user(self):
        """
        Test import user matches
        """
        self.assertEqual(self.release.user, unicode(self.doc['user']))

    def test_import_param_package_status(self):
        """
        Test package status attributes match
        """
        self.assertEqual(self.package.status, self.doc['packages'][0]['status'])

    def test_import_param_package_name(self):
        """
        Test package name attributes match
        """
        self.assertEqual(self.package.name, self.doc['packages'][0]['name'])

    def test_import_param_package_version(self):
        """
        Test package version attributes match
        """
        self.assertEqual(self.package.version, self.doc['packages'][0]['version'])

    def test_import_param_package_diff_url(self):
        """
        Test package diff_url attributes match
        """
        self.assertEqual(self.package.diff_url, self.doc['packages'][0]['diff_url'])

    def test_import_param_package_ftime(self):
        """
        Test package ftime attributes match
        """
        self.assertEqual(
            self.package.ftime.strftime(config.get('main', 'time_format')),
            self.doc['packages'][0]['ftime'])

    def test_import_param_package_stime(self):
        """
        Test package stime attributes match
        """
        self.assertEqual(
            self.package.stime.strftime(config.get('main', 'time_format')),
            self.doc['packages'][0]['stime'])
