from __future__ import print_function, unicode_literals
import arrow
import json
from tests.test_contract import OrloTest
import orlo.queries
from time import sleep

__author__ = 'alforbes'


"""
Test the /stats, /info urls and associated functions
"""


class OrloStatsFunctionTest(OrloTest):
    def test_user_summary(self):
        """
        Test that user_summary returns the expected output
        """
        for _ in range(0, 3):
            self._create_release(user='userOne')
        for _ in range(0, 2):
            self._create_release(user='userTwo')

        result = orlo.queries.user_summary().all()
        self.assertEqual(len(result), 2)

        for user, count in result:
            if user == 'userOne':
                self.assertEqual(count, 3)
            elif user == 'userTwo':
                self.assertEqual(count, 2)
            else:
                raise Exception('Unexpected user: {}'.format(str(user)))

    def test_user_summary_with_platform(self):
        """
        Test user_summary with a platform filter
        """
        for _ in range(0, 3):
            self._create_release(user='userOne', platforms=['platformOne'])
        for _ in range(0, 2):
            self._create_release(user='userTwo', platforms=['platformTwo'])

        result = orlo.queries.user_summary(platform='platformOne').all()
        self.assertEqual(len(result), 1)

        for user, count in result:
            if user == 'userOne':
                self.assertEqual(count, 3)
            else:
                raise Exception('Unexpected user: {}'.format(str(user)))

    def test_platform_summary(self):
        """
        Test platform_summary returns a summary
        """

        for _ in range(0, 3):
            self._create_release(platforms=['platformOne', 'platformTwo'])
        for _ in range(0, 2):
            self._create_release(platforms=['platformTwo', 'platformThree'])

        results = orlo.queries.platform_summary().all()
        for platform, count in results:
            if platform == 'platformOne':
                self.assertEqual(count, 3)
            elif platform == 'platformTwo':
                self.assertEqual(count, 5)
            elif platform == 'platformThree':
                self.assertEqual(count, 2)
            else:
                raise Exception('Unexpected platform: {}'.format(str(platform)))

    def test_releases_successful(self):
        """
        Test releases_successful in the simplest case
        """
        rid = self._create_finished_release()
        results = orlo.queries.releases_successful().all()
        ids = [str(u) for u, _ in results]
        self.assertIn(rid, ids)

    def test_releases_successful_with_platform(self):
        """
        Test releases_successful with a platform filter
        """
        rid = self._create_finished_release()
        results = orlo.queries.releases_successful(platform='test_platform').all()
        ids = [str(u) for u, _ in results]
        self.assertIn(rid, ids)

    def test_releases_successful_with_platform_excluded(self):
        """
        Test releases_successful with a platform filter excluding
        """
        rid = self._create_finished_release()
        results = orlo.queries.releases_successful(platform='bogus_platform').all()
        self.assertEqual(len(results), 0)

    def test_releases_successful_excludes_failed(self):
        """
        Test that releases_successful only returns successful releases by adding a failed one
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

        results = orlo.queries.releases_successful().all()
        ids = [str(u) for u, _ in results]

        self.assertNotIn(rid, ids)

    def test_package_list(self):
        """
        Test that package_list returns a list of all packages released
        """
        for _ in range(0, 3):
            rid = self._create_release()
            self._create_package(rid, name='packageOne')
            self._create_package(rid, name='packageTwo')

        result = orlo.queries.package_list().all()
        self.assertEqual(len(result), 2)
        packages = [r[0] for r in result]
        self.assertIn('packageOne', packages)
        self.assertIn('packageTwo', packages)

    def test_package_list_with_platform(self):
        """
        Test package_list with a platform filter
        """
        rid1 = self._create_release(platforms='platformOne')
        self._create_package(rid1, name='packageOne')

        rid2 = self._create_release(platforms='platformTwo')
        self._create_package(rid2, name='packageTwo')

        result = orlo.queries.package_list(platform='platformOne').all()
        self.assertEqual(len(result), 1)
        packages = [r[0] for r in result]
        self.assertIn('packageOne', packages)
        self.assertNotIn('packageTwo', packages)

    def test_package_summary(self):
        """
        Test package_summary
        """
        rid1 = self._create_release()
        self._create_package(rid1, name='packageOne')
        self._create_package(rid1, name='packageTwo')

        rid2 = self._create_release()
        self._create_package(rid2, name='packageOne')
        self._create_package(rid2, name='packageTwo')

        result = orlo.queries.package_summary().all()

        self.assertEqual(len(result), 2)
        packages = [r[0] for r in result]
        self.assertIn('packageOne', packages)
        self.assertIn('packageTwo', packages)

    def test_package_summary_with_platform(self):
        """
        Test package_summary
        """
        rid1 = self._create_release(platforms=['platformOne'])
        self._create_package(rid1, name='packageOne')

        rid2 = self._create_release(platforms=['platformTwo'])
        self._create_package(rid2, name='packageTwo')

        result = orlo.queries.package_summary(platform='platformOne').all()

        self.assertEqual(len(result), 1)
        packages = [r[0] for r in result]
        self.assertIn('packageOne', packages)

    def test_package_summary_with_stime(self):
        """
        Test package_summary with stime filter inclusive (hour in past)
        """
        rid1 = self._create_release()
        self._create_package(rid1, name='packageOne')

        hour_ago = arrow.utcnow().replace(hours=-1)
        result = orlo.queries.package_summary(stime=hour_ago).all()

        self.assertEqual(len(result), 1)
        packages = [r[0] for r in result]
        self.assertIn('packageOne', packages)

    def test_package_summary_with_stime_negative(self):
        """
        Test package_summary with stime filter exclusive (hour in future)
        """
        rid1 = self._create_release()
        self._create_package(rid1, name='packageOne')

        hour_future = arrow.utcnow().replace(hours=+1)
        result = orlo.queries.package_summary(stime=hour_future).all()

        self.assertEqual(len(result), 0)

    def test_package_summary_with_ftime(self):
        """
        Test package_summary with ftime filter inclusive (hour in future)
        """
        rid1 = self._create_release()
        self._create_package(rid1, name='packageOne')

        hour_future = arrow.utcnow().replace(hours=+1)
        result = orlo.queries.package_summary(ftime=hour_future).all()

        self.assertEqual(len(result), 1)
        packages = [r[0] for r in result]
        self.assertIn('packageOne', packages)

    def test_package_summary_with_ftime_negative(self):
        """
        Test package_summary with ftime filter exclusive (hour in past)
        """
        rid1 = self._create_release()
        self._create_package(rid1, name='packageOne')

        hour_past = arrow.utcnow().replace(hours=-1)
        result = orlo.queries.package_summary(ftime=hour_past).all()

        self.assertEqual(len(result), 0)

    def test_package_versions(self):
        """
        Test package_versions

        In this test, we create two releases. packageOne succeeds in both but packageTwo fails
        in the second, therefore the current version for packageOne should be the second release,
        but packageTwo should remain with the first version
        """
        rid1 = self._create_release(platforms=['foo'])
        pid1 = self._create_package(rid1, name='packageOne', version='1.0.1')
        pid2 = self._create_package(rid1, name='packageTwo', version='2.0.1')
        self._start_package(rid1, pid1)
        self._stop_package(rid1, pid1)
        self._start_package(rid1, pid2)
        self._stop_package(rid1, pid2)
        sleep(0.1)  # To ensure some time separation
        rid2 = self._create_release(platforms=['foo'])
        pid1 = self._create_package(rid2, name='packageOne', version='1.0.2')
        pid2 = self._create_package(rid2, name='packageTwo', version='2.0.2')
        self._start_package(rid2, pid1)
        self._stop_package(rid2, pid1)
        self._start_package(rid2, pid2)
        self._stop_package(rid2, pid2, success=False)

        result = orlo.queries.package_versions().all()
        self.assertEqual(len(result), 2)  # Two entries, packageOne/Two
        versions = [(p, v) for p, v, t in result]  # strip out the time
        # Correct versions:
        self.assertIn(('packageOne', '1.0.2'), versions)
        self.assertIn(('packageTwo', '2.0.1'), versions)

    def test_package_versions_with_platform(self):
        """
        Test package_versions excludes non-specified platforms
        """
        self._create_finished_release()  # this release should not appear in result
        rid1 = self._create_release(platforms=['foo'])
        pid1 = self._create_package(rid1, name='packageOne', version='1.0.1')
        self._start_package(rid1, pid1)
        self._stop_package(rid1, pid1)

        result = orlo.queries.package_versions(platform='foo').all()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], 'packageOne')


class OrloStatsUrlTest(OrloTest):
    def test_info_users(self):
        """
        Test /info/users returns 200
        """
        self._create_release(user='userOne')
        response = self.client.get('/info/users')
        self.assert200(response)
        self.assertIn('userOne', response.json)

    def test_info_platforms(self):
        """
        Test /info/platforms returns 200
        """
        self._create_release(platforms=['platformOne'])
        response = self.client.get('/info/platforms')
        self.assert200(response)
        self.assertIn('platformOne', response.json)

