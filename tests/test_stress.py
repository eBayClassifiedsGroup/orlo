from __future__ import print_function
from test_base import LiveDbTest
from test_orm import OrloDbTest
import json
import requests

__author__ = 'alforbes'


class StressTest(LiveDbTest):
    """ This test was to track down a database connection leak

    It stands because it detected the leak by stalling on db.drop_all() in
    the tearDown function
    """
    ITERATIONS = 1

    def setUp(self):
        super(StressTest, self).setUp()
        for i in range(0, self.ITERATIONS):
            if i+1 % 50 == 0:
                print('Creating release {}'.format(i+1))
            OrloDbTest._create_finished_release(success=True)

    def _get_releases(self, release_id=None, filters=None, expected_status=200):
        """
        Perform a GET to /releases with optional filters
        """

        if release_id:
            path = '{}/releases/{}'.format(self.uri, release_id)
        elif filters:
            path = '{}/releases?{}'.format(self.uri, '&'.join(filters))
        else:
            path = '{}/releases'.format(self.uri)

        results_response = requests.get(
            path, headers={'content_type': 'application/json'}
        )

        try:
            self.assertEqual(results_response.status_code, expected_status)
        except AssertionError as err:
            print(results_response.data)
            raise

        # r_json = json.loads(results_response.data.decode('utf-8'))
        return results_response.json

    def test_hammer_postgres(self):
        """ Hammer postgres and see if it times out """
        for i in range(0, self.ITERATIONS):
            print('get', i)
            self._get_releases(filters=['user=testuser'])

