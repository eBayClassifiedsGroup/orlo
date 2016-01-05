from __future__ import print_function
from tests.test_orm import OrloDbTest
import unittest

__author__ = 'alforbes'


class StatsTest(OrloDbTest):
    ENDPOINT = '/stats'

    def setUp(self):
        super(OrloDbTest, self).setUp()
        for r in range(0, 3):
            self._create_finished_release()

    def test_endpoint_200(self):
        """
        Test self.ENDPOINT returns 200
        """
        response = self.client.get(self.ENDPOINT)
        self.assert200(response)

    def test_endpoint_returns_dict(self):
        """
        Test self.ENDPOINT returns a dictionary
        """
        response = self.client.get(self.ENDPOINT)
        self.assertIsInstance(response.json, dict)

    def test_result_includes_normals(self):
        """
        Test the result includes a 'normal' field
        """
        response = self.client.get(self.ENDPOINT)
        for k, v in response.json.items():
            self.assertIn('successful', v['releases']['normal'])
            self.assertIn('failed', v['releases']['normal'])

    def test_result_includes_rollbacks(self):
        """
        Test the result includes a 'rollback' field
        """
        response = self.client.get(self.ENDPOINT)
        for k, v in response.json.items():
            self.assertIn('successful', v['releases']['rollback'])
            self.assertIn('failed', v['releases']['rollback'])

    def test_result_includes_totals(self):
        """
        Test the result includes a 'successful' field
        """
        response = self.client.get(self.ENDPOINT)
        for k, v in response.json.items():
            self.assertIn('successful', v['releases']['total'])
            self.assertIn('failed', v['releases']['total'])

    def test_with_invalid_stime(self):
        """
        Test that an invalid start time is handled gracefully
        """
        response = self.client.get(self.ENDPOINT + '?stime=foo')
        self.assert400(response)
        self.assertIn('message', response.json)


class UserStatsTest(StatsTest):
    ENDPOINT = '/stats/user'

    def test_stats_user_200_with_user(self):
        """
        Test that /stats/user/username returns 200
        """
        response = self.client.get(self.ENDPOINT + '/testuser')
        self.assert200(response)

    def test_stats_user_returns_dict_with_user(self):
        """
        Test that /stats/user/username returns a dictionary
        """
        response = self.client.get(self.ENDPOINT + '/testuser')
        self.assertIsInstance(response.json, dict)


class TeamStatsTest(StatsTest):
    ENDPOINT = '/stats/team'

    def test_stats_team_200_with_team(self):
        """
        Test that /stats/team/team_name returns 200
        """
        response = self.client.get(self.ENDPOINT + '/test%20team')
        self.assert200(response)

    def test_stats_team_returns_dict_with_team(self):
        """
        Test that /stats/team/team_name returns a dictionary
        """
        response = self.client.get(self.ENDPOINT + '/test%20team')
        self.assertIsInstance(response.json, dict)


class PlatformStatsTest(StatsTest):
    ENDPOINT = '/stats/platform'

    def test_stats_platform_200_with_platform(self):
        """
        Test that /stats/platform/platform_name returns 200
        """
        response = self.client.get(self.ENDPOINT + '/test_platform')
        self.assert200(response)


class PackageStatsTest(StatsTest):
    ENDPOINT = '/stats/package'

    def test_stats_package_200_with_package(self):
        """
        Test that /stats/package/package_name returns 200
        """
        response = self.client.get(self.ENDPOINT + '/test-package')
        self.assert200(response)

    def test_stats_package_returns_dict_with_package(self):
        """
        Test that /stats/package/package_name returns a dictionary
        """
        response = self.client.get(self.ENDPOINT + '/test-package')
        self.assertIsInstance(response.json, dict)

