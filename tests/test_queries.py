from __future__ import print_function, unicode_literals
import arrow
import json
from tests.test_orm import OrloDbTest
import orlo.queries
from time import sleep

__author__ = 'alforbes'


"""
Test the query functions in queries.py

They work for now, but breaking the API urls will cause these to fail which could be confusing.
"""


class OrloQueryTest(OrloDbTest):
    pass


class SummaryTest(OrloQueryTest):
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

        result = orlo.queries.platform_summary().all()
        for platform, count in result:
            if platform == 'platformOne':
                self.assertEqual(count, 3)
            elif platform == 'platformTwo':
                self.assertEqual(count, 5)
            elif platform == 'platformThree':
                self.assertEqual(count, 2)
            else:
                raise Exception('Unexpected platform: {}'.format(str(platform)))

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
        rid1 = self._create_release(platforms=['platformOne'])
        self._create_package(rid1, name='packageOne')

        rid2 = self._create_release(platforms=['platformTwo'])
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
        self._start_package(pid1)
        self._stop_package(pid1)
        self._start_package(pid2)
        self._stop_package(pid2)
        sleep(0.1)  # To ensure some time separation
        rid2 = self._create_release(platforms=['foo'])
        pid1 = self._create_package(rid2, name='packageOne', version='1.0.2')
        pid2 = self._create_package(rid2, name='packageTwo', version='2.0.2')
        self._start_package(pid1)
        self._stop_package(pid1)
        self._start_package(pid2)
        self._stop_package(pid2, success=False)

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
        self._start_package(pid1)
        self._stop_package(pid1)

        result = orlo.queries.package_versions(platform='foo').all()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], 'packageOne')


class ReleasesSuccessful(OrloQueryTest):
    def setUp(self):
        super(OrloDbTest, self).setUp()

    def test_releases_successful(self):
        """
        Test count_releases_successful in the simplest case
        """
        self._create_finished_release()
        result = orlo.queries.count_releases_successful().all()
        self.assertEqual(1, result[0][0])

    def test_releases_successful_length(self):
        """
        Test that the function returns the correct number of items
        """
        for _ in range(0, 3):
            self._create_finished_release()
        result = orlo.queries.count_releases_successful().all()
        self.assertEqual(1, len(result))

    def test_releases_successful_with_user(self):
        """
        Test count_releases_successful with a user
        """
        self._create_finished_release()
        result = orlo.queries.count_releases_successful(user='testuser').all()
        self.assertEqual(1, result[0][0])

    def test_releases_successful_with_user_excluded(self):
        """
        Test count_releases_successful with a user
        """
        self._create_finished_release()
        result = orlo.queries.count_releases_successful(user='bogus_user').all()
        self.assertEqual(0, result[0][0])

    def test_releases_successful_with_team(self):
        """
        Test count_releases_successful with a team
        """
        self._create_finished_release()
        result = orlo.queries.count_releases_successful(team='test team').all()
        self.assertEqual(1, result[0][0])

    def test_releases_successful_with_team_excluded(self):
        """
        Test count_releases_successful with a team excluded
        """
        self._create_finished_release()
        result = orlo.queries.count_releases_successful(team='bogus team').all()
        self.assertEqual(0, result[0][0])

    def test_releases_successful_with_package(self):
        """
        Test count_releases_successful with a package
        """
        self._create_finished_release()
        result = orlo.queries.count_releases_successful(package='test-package').all()
        self.assertEqual(1, result[0][0])

    def test_releases_successful_with_package_excluded(self):
        """
        Test count_releases_successful with a package
        """
        self._create_finished_release()
        result = orlo.queries.count_releases_successful(package='bogus-package').all()
        self.assertEqual(0, result[0][0])

    def test_releases_successful_with_platform(self):
        """
        Test count_releases_successful with a platform filter
        """
        self._create_finished_release()
        result = orlo.queries.count_releases_successful(platform='test_platform').all()
        self.assertEqual(1, result[0][0])

    def test_releases_successful_with_platform_excluded(self):
        """
        Test count_releases_successful with a platform filter excluding
        """
        self._create_finished_release()
        result = orlo.queries.count_releases_successful(platform='bogus_platform').all()
        self.assertEqual(0, result[0][0])

    def test_releases_successful_excludes_failed(self):
        """
        Test that count_releases_successful only returns successful releases by adding a failed one
        """

        for _ in range(0, 3):
            # 3 complete, successful releases
            self._create_finished_release()

        # And a fourth with one failed package (should not be present)
        rid = self._create_release()
        pid1 = self._create_package(rid)
        pid2 = self._create_package(rid)
        self._start_package(pid1)
        self._start_package(pid2)
        self._stop_package(pid1, success=True)
        self._stop_package(pid2, success=False)
        self._stop_release(rid)

        result = orlo.queries.count_releases_successful().all()
        self.assertEqual(3, result[0][0])

