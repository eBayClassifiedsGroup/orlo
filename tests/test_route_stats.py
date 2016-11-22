from __future__ import print_function
from test_orm import OrloDbTest
import arrow
import unittest

__author__ = 'alforbes'


class TestStats(OrloDbTest):
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


class TestUserStats(TestStats):
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


class TestTeamStats(TestStats):
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


class TestPlatformStats(TestStats):
    ENDPOINT = '/stats/platform'

    def test_stats_platform_200_with_platform(self):
        """
        Test that /stats/platform/platform_name returns 200
        """
        response = self.client.get(self.ENDPOINT + '/test_platform')
        self.assert200(response)


class TestPackageStats(TestStats):
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


class TestStatsByDateRelease(TestStats):
    """
    Testing the "by_date" urls
    """
    ENDPOINT = '/stats/by_date/release'

    def test_result_includes_normals(self):
        unittest.skip("Not suitable test for this endpoint")

    def test_result_includes_rollbacks(self):
        unittest.skip("Not suitable test for this endpoint")

    def test_result_includes_totals(self):
        unittest.skip("Not suitable test for this endpoint")

    def test_with_invalid_stime(self):
        # TODO the stats endpoints should be made consistent with the others by calling
        # apply_filters on the query parameters
        unittest.skip("Not suitable test for this endpoint")

    def test_stats_by_date_with_year(self):
        """
        Test /stats/by_date/year
        """
        year = arrow.utcnow().year
        response = self.client.get(self.ENDPOINT + '?stime_gt={}-01-01'.format(year))
        self.assert200(response)

    def test_stats_by_date_with_year_month(self):
        """
        Test /stats/by_date/year
        """
        year = arrow.utcnow().year
        month = arrow.utcnow().month
        response = self.client.get(self.ENDPOINT + '?stime_gt={}-{}-01'.format(year, month))
        self.assert200(response)

    def test_stats_by_date_with_unit_day(self):
        """
        Test /stats/by_date/year
        """
        response = self.client.get(self.ENDPOINT + '?unit=day')
        self.assert200(response)

    def test_stats_by_date_with_summarize_by_unit_day(self):
        """
        Test /stats/by_date/year
        """
        response = self.client.get(self.ENDPOINT + '?unit=day&summarize_by_unit=1')
        self.assert200(response)

    def test_stats_by_date_with_platform_filter(self):
        """
        Test /stats/by_date with a platform filter
        """
        year = str(arrow.utcnow().year)
        response = self.client.get(self.ENDPOINT + '?platform=test_platform')
        self.assert200(response)
        self.assertIn(year, response.json)

    def test_stats_by_date_with_platform_filter_negative(self):
        """
        Test /stats/by_date with a bad platform filter returns nothing
        """
        response = self.client.get(self.ENDPOINT + '?platform=bad_platform_foo')
        self.assert200(response)
        self.assertEqual({}, response.json)


class TestStatsByDatePackage(OrloDbTest):
    """
    Testing the "by_date" urls
    """
    ENDPOINT = '/stats/by_date/package'

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

    def test_package_name_in_dict(self):
        """
        Test the package name is in the returned json
        """
        response = self.client.get(self.ENDPOINT)
        year = str(arrow.utcnow().year)
        month = str(arrow.utcnow().month)
        self.assertIn('test-package', response.json[year][month])
