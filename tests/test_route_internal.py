from __future__ import print_function
from test_route_base import OrloHttpTest

__author__ = 'alforbes'


class TestInternalRoute(OrloHttpTest):
    def test_version(self):
        """
        Test /version returns 200
        """
        response = self.client.get('/internal/version')
        self.assert200(response)
        self.assertIn('version', response.json)
