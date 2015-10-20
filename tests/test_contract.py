from __future__ import print_function
import sponge
import json
import uuid
from flask.ext.testing import TestCase
from sponge.orm import db


class SpongeTest(TestCase):
    """
    Base test class
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


class ContractTest(SpongeTest):
    """
    Test the api views

    Most of these are dependant on prior tests, because for example to test
    package stop, we first need a package that has been started. Thus failures
    in tests earlier in the workflow will cause later tests to fail as well.
    """

    def test_ping(self):
        """
        Start with something simple
        """
        response = self.client.get('/ping')
        self.assert200(response)
        self.assertEqual(response.data, 'pong')

    def test_create_release(self):
        """
        Create a release

        Return the response so it can be used by other tests
        """
        response = self.client.post('/releases',
            data=json.dumps({
                'note': 'test note asdf',
                'platforms': ['test_platform'],
                'references': ['TestTicket-123'],
                'team': 'Test Team',
                'user': 'testuser',
            }),
            content_type='application/json',
        )
        self.assert200(response)

        release_id = response.json['id']
        self.assertEqual(uuid.UUID(release_id).get_version(), 4)

        return release_id

    def test_create_package(self):
        """
        Create a package

        Calls create_release first, and returns both ids for future tests
        """
        release_id = self.test_create_release()

        package_response = self.client.post(
            '/releases/{}/packages'.format(release_id),
            data=json.dumps({
                'name': 'test-package',
                'version': '1.2.3'
            }),
            content_type='application/json',
        )
        self.assert200(package_response)

        package_id = package_response.json['id']
        self.assertEqual(uuid.UUID(package_id).get_version(), 4)

        return release_id, package_id

    def test_add_results(self):
        """
        Add the results of a package deploy
        """
        release_id, package_id = self.test_create_package()

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

        release_id, package_id = self.test_create_package()
        results_response = self.client.post(
            '/releases/{}/packages/{}/start'.format(release_id, package_id),
            content_type='application/json',
        )
        self.assertEqual(results_response.status_code, 204)
        return release_id, package_id

    def test_package_stop(self):
        """
        Test stopping a package

        Calls test_package start first as we need one that has started
        """

        release_id, package_id = self.test_package_start()
        results_response = self.client.post(
            '/releases/{}/packages/{}/stop'.format(release_id, package_id),
            data=json.dumps({
                'success': 'true',
                'foo': 'bar',
            }),
            content_type='application/json',
        )
        self.assertEqual(results_response.status_code, 204)

        # for test_release_stop
        return release_id

    def test_release_stop(self):
        """
        Test stopping a release

        As before, calls all the others as we need a full workflow present
        """
        release_id = self.test_package_stop()
        results_response = self.client.post(
            '/releases/{}/stop'.format(release_id),
            content_type='application/json',
        )

        self.assertEqual(results_response.status_code, 204)

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

    def test_get_release(self):
        """
        Test the list of releases
        """
        for _ in range(0, 2):
            self.test_release_stop()

        results_response = self.client.get(
            '/releases',
            content_type='application/json',
        )
        self.assertEqual(results_response.status_code, 200)
        r_json = json.loads(results_response.data)
        self.assertEqual(len(r_json['releases']), 2)
