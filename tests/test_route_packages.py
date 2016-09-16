from __future__ import print_function
from test_route_base import OrloHttpTest
import json

__author__ = 'alforbes'


class GetPackagesTest(OrloHttpTest):
    """
    Test the HTTP GET contract
    """

    def _get_packages(self, package_id=None, filters=None, expected_status=200):
        """
        Perform a GET to /releases with optional filters
        """

        if package_id:
            path = '/packages/{}'.format(package_id)
        elif filters:
            path = '/packages?{}'.format('&'.join(filters))
        else:
            path = '/packages'

        results_response = self.client.get(
            path, content_type='application/json',
        )

        try:
            self.assertEqual(results_response.status_code, expected_status)
        except AssertionError as err:
            print(results_response.data)
            raise
        r_json = json.loads(results_response.data.decode('utf-8'))
        return r_json

    def test_packages(self):
        """
        Test that we get 400 and a message with no params
        """
        response = self.client.get('/packages')
        self.assert400(response)
        self.assertIn('message', response.json)

    def test_get_single_package(self):
        """
        Fetch a single release
        """
        release_id = self._create_release()
        package_id = self._create_package(release_id)
        p = self._get_packages(package_id=package_id)
        self.assertEqual(1, len(p['packages']))
        self.assertEqual(package_id, p['packages'][0]['id'])

    def test_get_package_multiple(self):
        """
        Fetch multiple packages
        """
        for _ in range(0, 3):
            self._create_finished_release()
        p = self._get_packages(filters=['name=test-package'])
        self.assertIsInstance(p['packages'], list)
        self.assertEqual(3, len(p['packages']))

