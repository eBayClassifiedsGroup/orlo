from __future__ import print_function, unicode_literals
import json
from orlo.orm import Release, Package, Platform, db
from orlo.config import config
from tests.test_contract import OrloTest
from orlo.route_stats import get_summary_users, get_summary_platforms, get_successful_releases

__author__ = 'alforbes'


class OrloStatsFunctionTest(OrloTest):
    def test_get_summary_users(self):
        """
        Test that get_summary_users returns the expected output
        """
        for _ in range(0, 3):
            self._create_release(user='userOne')
        for _ in range(0, 2):
            self._create_release(user='userTwo')

        result = get_summary_users()
        self.assertEqual(len(result), 2)

        for user, count in result:
            if user == 'userOne':
                self.assertEqual(count, 3)
            elif user == 'userTwo':
                self.assertEqual(count, 2)
            else:
                raise Exception('Unexpected user: {}'.format(str(user)))

    def test_get_summary_users_with_platform(self):
        """
        Test get_summary_users with a platform filter
        """
        for _ in range(0, 3):
            self._create_release(user='userOne', platforms=['platformOne'])
        for _ in range(0, 2):
            self._create_release(user='userTwo', platforms=['platformTwo'])

        result = get_summary_users(platform='platformOne')
        self.assertEqual(len(result), 1)

        for user, count in result:
            if user == 'userOne':
                self.assertEqual(count, 3)
            else:
                raise Exception('Unexpected user: {}'.format(str(user)))

    def test_get_summary_platforms(self):
        """
        Test get_summary_platforms returns a summary
        """

        for _ in range(0, 3):
            self._create_release(platforms=['platformOne', 'platformTwo'])
        for _ in range(0, 2):
            self._create_release(platforms=['platformTwo', 'platformThree'])

        results = get_summary_platforms()
        for platform, count in results:
            if platform == 'platformOne':
                self.assertEqual(count, 3)
            elif platform == 'platformTwo':
                self.assertEqual(count, 5)
            elif platform == 'platformThree':
                self.assertEqual(count, 2)
            else:
                raise Exception('Unexpected platform: {}'.format(str(platform)))

    def test_get_successful_releases(self):
        """
        Test get_successful_releases in the simplest case
        """
        rid = self._create_finished_release()
        results = get_successful_releases()
        ids = [str(u) for u, _ in results]
        self.assertIn(rid, ids)

    def test_get_successful_releases_with_platform(self):
        """
        Test get_successful_releases with a platform filter
        """
        rid = self._create_finished_release()
        results = get_successful_releases(platform='test_platform')
        ids = [str(u) for u, _ in results]
        self.assertIn(rid, ids)

    def test_get_successful_releases_with_platform_excluded(self):
        """
        Test get_successful_releases with a platform filter excluding
        """
        rid = self._create_finished_release()
        results = get_successful_releases(platform='bogus_platform')
        self.assertEqual(len(results), 0)

    def test_get_successful_releases_excludes_failed(self):
        """
        Test that get_successful_releases only returns successful releases by adding a failed one
        """

        for _ in range(0, 3):
            # 3 complete, successful releases
            self._create_finished_release()

        # And a fourth with one incomplete package (should not be present)
        rid = self._create_release()
        pid1 = self._create_package(rid)
        pid2 = self._create_package(rid)
        # Just complete the last one
        self._start_package(rid, pid1)
        self._start_package(rid, pid2)
        self._stop_package(rid, pid1, success=True)
        self._stop_package(rid, pid2, success=False)
        self._stop_release(rid)

        results = get_successful_releases()
        ids = [str(u) for u, _ in results]

        self.assertNotIn(rid, ids)


class OrloStatsUrlTest(OrloTest):
    def test_info_users(self):
        """
        Test /info/users returns 200
        """
        self._create_release(user='userOne')
        response = self.client.get('/info/users')
        self.assert200(response)
        self.assertIn('userOne', response.json)

