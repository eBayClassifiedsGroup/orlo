from __future__ import print_function, unicode_literals
from datetime import datetime, timedelta
import json
import uuid
from orlo.orm import db, Package, Release
from orlo.config import config
from time import sleep
from test_base import OrloTest


class OrloHttpTest(OrloTest):
    """
    Base class for tests which contains the methods required to move
    releases and packages through the workflow via HTTP
    """

    def _create_release(self,
                        user='testuser',
                        team='test team',
                        platforms='test_platform',
                        references='TestTicket-123',
                        ):
        """
        Create a release using the REST API

        :param user:
        :param team:
        :param platforms:
        :param references:
        :return: the release ID
        """

        response = self.client.post(
            '/releases',
            data=json.dumps({
                'note': 'test note lorem ipsum',
                'metadata': {'env': 'test'},
                'platforms': platforms,
                'references': references,
                'team': team,
                'user': user,
            }),
            content_type='application/json',
        )
        self.assert200(response)
        return response.json['id']

    def _create_package(self, release_id,
                        name='test-package',
                        version='1.2.3',
                        diff_url=None,
                        rollback=False,
                        ):
        """
        Create a package using the REST API

        :param release_id: release id to create the package for
        :param name:
        :param version:
        :param diff_url:
        :param rollback:
        :return: package id
        """
        doc = {
            'name': name,
            'version': version,
        }

        if diff_url:
            doc['diff_url'] = diff_url
        if rollback:
            doc['rollback'] = rollback

        response = self.client.post(
            '/releases/{}/packages'.format(release_id),
            data=json.dumps(doc),
            content_type='application/json',
        )
        self.assert200(response)
        return response.json['id']

    def _start_package(self, release_id, package_id):
        """
        Start a package using the REST API

        :param release_id:
        :return:
        """

        response = self.client.post(
            '/releases/{}/packages/{}/start'.format(release_id, package_id),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 204)
        return response

    def _stop_package(self, release_id, package_id,
                      success=True):
        """
        Start a package using the REST API

        :param release_id:
        :return:
        """

        response = self.client.post(
            '/releases/{}/packages/{}/stop'.format(release_id, package_id),
            data=json.dumps({
                'success': str(success),
                'foo': 'bar',
            }),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 204)
        return response

    def _stop_release(self, release_id):
        """
        Stop a release using the REST API

        :param release_id:
        :return:
        """
        response = self.client.post(
            '/releases/{}/stop'.format(release_id),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 204)
        return response

    def _create_finished_release(self):
        """
        Create a completed release, with default values, that has gone through
        the whole workflow
        """
        release_id = self._create_release()
        package_id = self._create_package(release_id)

        self._start_package(release_id, package_id)
        self._stop_package(release_id, package_id)
        self._stop_release(release_id)

        return release_id

    def _post_releases_notes(self, release_id, text):
        """
        Add a note to a release
        """

        doc = {'text': text}
        response = self.client.post(
            '/releases/{}/notes'.format(release_id, text),
            data=json.dumps(doc),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 204)
        return response

    def _post_releases_metadata(self, release_id, metadata):
        """
        Add a metadata to a release
        """

        response = self.client.post(
            '/releases/{}/metadata'.format(release_id, metadata),
            data=json.dumps(metadata),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 204)
        return response


class BaseUrlTest(OrloHttpTest):
    """
    Test the HTTP GET contract
    """
    def test_ping(self):
        """
        Start with something simple
        """
        response = self.client.get('/ping')
        self.assert200(response)
        self.assertEqual('pong', response.json['message'])

    def test_version(self):
        """
        Test the version url
        """
        from orlo import __version__
        response = self.client.get('/version')
        self.assert200(response)
        self.assertEqual(__version__, response.json['version'])
