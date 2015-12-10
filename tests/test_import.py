from __future__ import print_function, unicode_literals
import json
from orlo.orm import Release, Package, Platform, db
from orlo.config import config
from orlo.util import string_to_list
from tests.test_contract import OrloTest

__author__ = 'alforbes'


class ImportTest(OrloTest):
    doc = """
    [
        {
          "platforms": [ "GumtreeUK" ],
          "ftime": "2015-12-09T12:34:45Z",
          "stime": "2015-12-09T12:34:45Z",
          "team": "Gumtree UK Site Operations",
          "references": [ "GTEPICS-TEST3" ],
          "packages": [
            {
              "status": "SUCCESSFUL",
              "rollback": true,
              "name": "test-package-1",
              "version": "0.0.1",
              "ftime": "2015-12-09T12:34:45Z",
              "stime": "2015-12-09T12:34:45Z",
              "diff_url": "http://example.com/diff"
            },
            {
              "status": "SUCCESSFUL",
              "rollback": true,
              "name": "test-package-2",
              "version": "0.0.2",
              "ftime": "2015-12-09T12:34:45Z",
              "stime": "2015-12-09T12:34:45Z",
              "diff_url": null
            }
          ],
          "user": "bob"
        }
    ]
    """
    doc_dict = json.loads(doc)

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
            '/releases/import',
            data=self.doc,
            content_type='application/json',
        )

        # self.assert200(response)
        self.release = db.session.query(Release).first()
        self.package = db.session.query(Package).first()
        self.platform = db.session.query(Platform).first()

    def test_import_param_platforms(self):
        """
        Test that the platforms field is imported successfully
        """
        self.assertEqual(self.platform.name, self.doc_dict[0]['platforms'][0])

    def test_import_param_ftime(self):
        """
        Test finish time matches
        """

        self.assertEqual(
            self.release.ftime.strftime(config.get('main', 'time_format')),
            self.doc_dict[0]['stime'])

    def test_import_param_stime(self):
        """
        Test start time matches
        """
        self.assertEqual(
            self.release.stime.strftime(config.get('main', 'time_format')),
            self.doc_dict[0]['stime'])

    def test_import_param_team(self):
        """
        Test imported team matches
        """
        self.assertEqual(self.release.team, self.doc_dict[0]['team'])

    def test_import_param_references(self):
        """
        Test imported references match
        """
        self.assertEqual(self.release.references, unicode(self.doc_dict[0]['references']))

    def test_import_param_user(self):
        """
        Test import user matches
        """
        self.assertEqual(self.release.user, unicode(self.doc_dict[0]['user']))

    def test_import_param_package_status(self):
        """
        Test package status attributes match
        """
        self.assertEqual(self.package.status, self.doc_dict[0]['packages'][0]['status'])

    def test_import_param_package_name(self):
        """
        Test package name attributes match
        """
        self.assertEqual(self.package.name, self.doc_dict[0]['packages'][0]['name'])

    def test_import_param_package_version(self):
        """
        Test package version attributes match
        """
        self.assertEqual(self.package.version, self.doc_dict[0]['packages'][0]['version'])

    def test_import_param_package_diff_url(self):
        """
        Test package diff_url is recorded
        """
        self.assertEqual(self.package.diff_url, self.doc_dict[0]['packages'][0]['diff_url'])

    def test_import_param_package_ftime(self):
        """
        Test package ftime attributes match
        """
        self.assertEqual(
            self.package.ftime.strftime(config.get('main', 'time_format')),
            self.doc_dict[0]['packages'][0]['ftime'])

    def test_import_param_package_stime(self):
        """
        Test package stime attributes match
        """
        self.assertEqual(
            self.package.stime.strftime(config.get('main', 'time_format')),
            self.doc_dict[0]['packages'][0]['stime'])
