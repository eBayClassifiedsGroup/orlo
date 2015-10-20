from __future__ import print_function
import sponge
import json
import uuid
from flask.ext.testing import TestCase
from sponge.orm import db


class SpongeTest(TestCase):
    """
    Base class for tests which contains the methods required to move
    releases and packages through the workflow
    """

    def create_app(self):
        app = sponge.app
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
        app.config['TESTING'] = True
        app.config['DEBUG'] = True
        app.config['TRAP_HTTP_EXCEPTIONS'] = True
        app.config['PRESERVE_CONTEXT_ON_EXCEPTION'] = False

        return sponge.app

    def setUp(self):
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def _create_release(self,
                        user='testuser',
                        team='test team',
                        platform='test_platform',
                        reference='TestTicket-123',
                        ):
        """
        Create a release using the REST API

        :param user:
        :param team:
        :param platform:
        :param reference:
        :return: the release ID
        """

        response = self.client.post(
            '/releases',
            data=json.dumps({
                'note': 'test note lorem ipsum',
                'platforms': [platform],
                'references': [reference],
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
                        ):
        """
        Create a package using the REST API

        :param release_id: release id to create the package for
        :param name:
        :param version:
        :return: package id
        """

        response = self.client.post(
            '/releases/{}/packages'.format(release_id),
            data=json.dumps({
                'name': name,
                'version': version,
            }),
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


class PostContractTest(SpongeTest):
    """
    Test the HTTP POST contract
    """

    def test_create_release(self):
        """
        Create a release
        """
        release_id = self._create_release()
        self.assertEqual(uuid.UUID(release_id).get_version(), 4)

    def test_create_package(self):
        """
        Create a package
        """
        release_id = self._create_release()
        package_id = self._create_package(release_id)
        self.assertEqual(uuid.UUID(package_id).get_version(), 4)

    def test_add_results(self):
        """
        Add the results of a package deploy
        """
        release_id = self._create_release()
        package_id = self._create_package(release_id)

        results_response = self.client.post(
            '/releases/{}/packages/{}/results'.format(
                release_id, package_id),
            data=json.dumps({
                'success': 'true',
                'foo': 'bar',
            }),
            content_type='application/json',
        )
        self.assertEqual(results_response.status_code, 204)

    def test_package_start(self):
        """
        Test starting a package
        """
        release_id = self._create_release()
        package_id = self._create_package(release_id)

        return release_id, package_id

    def test_package_stop(self):
        """
        Test stopping a package
        """
        release_id = self._create_release()
        package_id = self._create_package(release_id)
        self._start_package(release_id, package_id)
        self._stop_package(release_id, package_id)

    def test_release_stop(self):
        """
        Test stopping a release

        As before, calls all the others as we need a full workflow present
        """
        release_id = self._create_release()
        package_id = self._create_package(release_id)
        self._start_package(release_id, package_id)
        self._stop_package(release_id, package_id)
        self._stop_release(release_id)

    def test_create_release_minimal(self):
        """
        Create a release, omitting all optional parameters
        """
        response = self.client.post('/releases',
            data=json.dumps({
                'platforms': ['test_platform'],
                'user': 'testuser',
            }),
            content_type='application/json',
        )
        self.assert200(response)


class GetContractTest(SpongeTest):
    """
    Test the HTTP GET contract
    """

    def _get_release(self, filters=None):
        """
        Perform a GET to /releases with optional filters
        """

        if filters:
            path = '/releases?{}'.format('&'.join(filters))
        else:
            path = '/releases'

        results_response = self.client.get(
            path, content_type='application/json',
        )
        self.assertEqual(results_response.status_code, 200)
        r_json = json.loads(results_response.data)
        return r_json

    def test_ping(self):
        """
        Start with something simple
        """
        response = self.client.get('/ping')
        self.assert200(response)
        self.assertEqual(response.data, 'pong')

    def test_get_release(self):
        """
        Test the list of releases
        """
        for _ in range(0, 3):
            self._create_finished_release()
        results = self._get_release()
        self.assertEqual(len(results['releases']), 3)

    def test_get_release_filter_package(self):
        """
        Filter on releases that contain a package
        """
        for _ in range(0, 3):
            self._create_finished_release()

        release_id = self._create_release()
        package_id = self._create_package(release_id, name='specific-package')
        results = self._get_release(filters=[
            'package_name=specific-package'
            ])

        for r in results['releases']:
            for p in r['packages']:
                self.assertEqual(p['name'], 'specific-package')
                self.assertEqual(p['id'], package_id)

        self.assertEqual(len(results['releases']), 1)

    def test_get_release_filter_user(self):
        """
        Filter on releases that were performed by a user
        """
        pass

    def test_get_release_filter_platform(self):
        """
        Filter on releases that were on a particular platform
        """
        pass

    def test_get_release_filter_stime_before(self):
        """
        Filter on releases that started before a particular time
        """
        pass

    def test_get_release_filter_stime_after(self):
        """
        Filter on releases that started after a particular time
        """
        pass

    def test_get_release_filter_ftime_before(self):
        """
        Filter on releases that finished before a particular time
        """
        pass

    def test_get_release_filter_ftime_after(self):
        """
        Filter on releases that finished after a particular time
        """
        pass

    def test_get_release_filter_duration_less(self):
        """
        Filter on releases that took less than x seconds
        """
        pass

    def test_get_release_filter_duration_greater(self):
        """
        Filter on releases that took greater than x seconds
        """
        pass

    def test_get_release_filter_team(self):
        """
        Filter on releases that a team was responsible for
        """
        pass
