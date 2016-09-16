from __future__ import print_function, unicode_literals
import arrow
import json
from test_orm import OrloDbTest
import orlo.queries
import orlo.exceptions
import orlo.stats
from time import sleep
import sqlalchemy.orm
import uuid
from orlo.util import is_uuid

__author__ = 'alforbes'


"""
Test the query functions in queries.py
"""


class OrloQueryTest(OrloDbTest):
    pass


class TestList(OrloQueryTest):
    def test_user_list(self):
        """
        Test that user_list returns a list of all users that have released
        """
        self._create_release(user='userOne')
        self._create_release(user='userTwo')

        result = orlo.queries.user_list().all()
        self.assertEqual(len(result), 2)
        users = [r[0] for r in result]
        self.assertIn('userOne', users)
        self.assertIn('userTwo', users)

    def test_user_list_with_platform(self):
        """
        Test user_list with a platform filter
        """
        self._create_release(user='userOne', platforms=['platformOne'])
        self._create_release(user='userTwo', platforms=['platformTwo'])

        result = orlo.queries.user_list(platform='platformOne').all()
        self.assertEqual(len(result), 1)
        users = [r[0] for r in result]
        self.assertIn('userOne', users)
        self.assertNotIn('userTwo', users)

    def test_user_list_with_duplicates(self):
        """
        Test that user_list does returns distinct user names
        """
        self._create_release(user='userOne')
        self._create_release(user='userOne')
        self._create_release(user='userTwo')

        result = orlo.queries.user_list().all()
        self.assertEqual(len(result), 2)
        users = [r[0] for r in result]
        self.assertIn('userOne', users)
        self.assertIn('userTwo', users)

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

    def test_platform_list(self):
        """
        Test that platform_list returns a list of all platforms that have been released to
        """
        self._create_release(platforms=['platformOne', 'platformTwo'])
        result = orlo.queries.platform_list().all()

        self.assertEqual(len(result), 2)
        platforms = [r[0] for r in result]
        self.assertIn('platformOne', platforms)
        self.assertIn('platformTwo', platforms)


class TestSummary(OrloQueryTest):
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

    def test_package_summary_returns_query(self):
        rid1 = self._create_release()
        self._create_package(rid1, name='packageOne')

        result = orlo.queries.package_summary()
        self.assertIsInstance(result, sqlalchemy.orm.query.Query)

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
        rid1 = self._create_release(platforms=['platformOne'])
        pid1 = self._create_package(rid1, name='packageOne', version='1.0.1')
        pid2 = self._create_package(rid1, name='packageTwo', version='2.0.1')
        self._start_package(pid1)
        self._stop_package(pid1)
        self._start_package(pid2)
        self._stop_package(pid2)
        sleep(0.1)  # To ensure some time separation
        rid2 = self._create_release(platforms=['platformOne'])
        pid1 = self._create_package(rid2, name='packageOne', version='1.0.2')
        pid2 = self._create_package(rid2, name='packageTwo', version='2.0.2')
        self._start_package(pid1)
        self._stop_package(pid1)
        self._start_package(pid2)
        self._stop_package(pid2, success=False)

        result = orlo.queries.package_versions().all()
        self.assertEqual(len(result), 2)  # Two entries, packageOne/Two
        versions = [(p, v) for p, v in result]  # strip out the time
        # Correct versions:
        self.assertIn(('packageOne', '1.0.2'), versions)
        self.assertIn(('packageTwo', '2.0.1'), versions)

    def test_package_versions_with_platform(self):
        """
        Test package_versions excludes non-specified platforms
        """
        self._create_finished_release()  # this release should not appear in result
        rid1 = self._create_release(platforms=['specific_platform'])
        pid1 = self._create_package(rid1, name='packageOne', version='1.0.1')
        self._start_package(pid1)
        self._stop_package(pid1)

        result = orlo.queries.package_versions(platform='specific_platform').all()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], 'packageOne')

    def test_package_versions_with_rollback(self):
        """
        Test package_versions with a rollback

        We should return the versions that were rolled back to and not exclude them
        """
        rid1 = self._create_release(platforms=['platformOne'])
        pid1 = self._create_package(rid1, name='packageOne', version='1.0.2')
        self._start_package(pid1)
        self._stop_package(pid1)
        sleep(0.1)  # To ensure some time separation
        rid2 = self._create_release(platforms=['platformOne'])
        pid1 = self._create_package(rid2, name='packageOne', version='1.0.1', rollback=True)
        self._start_package(pid1)
        self._stop_package(pid1)

        result = orlo.queries.package_versions().all()
        self.assertEqual(len(result), 1)  # One entry, packageOne
        versions = [(p, v) for p, v in result]  # strip out the time
        # Correct versions:
        self.assertIn(('packageOne', '1.0.1'), versions)


class TestInfo(OrloQueryTest):
    """
    Test the _info functions
    """

    def _create_test_package(self):
        rid = self._create_release(platforms=['platformOne'])
        pid = self._create_package(rid, name='packageOne', version='1.0.1')
        return pid

    def test_returns_query(self):
        """
        Assert that package_info should return a query
        """
        self._create_test_package()
        result = orlo.queries.package_info('packageOne')
        self.assertIsInstance(result, sqlalchemy.orm.query.Query)


class TestCountReleases(OrloQueryTest):
    """
    Parent class for testing the CountReleases function

    By subclassing it and overriding ARGS, we can test different combinations of
    arguments with the same test code.

    INCLUSIVE_ARGS represents a set of arguments that will match the releases
    created (see the functions in OrloQueryTest for what those are)
    EXCLUSIVE_ARGS represents a set of arguments that will not match any
    releases created, i.e. should return a count of zero

    This parent class has tests that should be the same result no matter what
    the arguments (except the exclusive case which must always a count of zero
    so we define it here)
    """

    INCLUSIVE_ARGS = {}  # Args we are testing, result should include these
    EXCLUSIVE_ARGS = {'user': 'non-existent'}  # Args which result in zero

    def test_count_releases(self):
        """
        Test count_releases in the simplest case
        """
        self._create_finished_release()
        result = orlo.queries.count_releases(**self.INCLUSIVE_ARGS).all()
        self.assertEqual(1, result[0][0])

    def test_count_releases_length(self):
        """
        Test that the function returns the correct number of items
        """
        for _ in range(0, 3):
            self._create_finished_release()
        # Should still only return one result (a count)
        result = orlo.queries.count_releases(**self.INCLUSIVE_ARGS).all()
        self.assertEqual(1, len(result))

    def test_count_releases_inclusive(self):
        """
        Test count_releases returns a count of one when filtering on INCLUSIVE_ARGS
        """
        self._create_finished_release()
        result = orlo.queries.count_releases(**self.INCLUSIVE_ARGS).all()
        self.assertEqual(1, result[0][0])

    def test_count_releases_exclusive(self):
        """
        Test count_releases returns a count of zero when filtering on EXCLUSIVE_ARGS
        """
        self._create_finished_release()
        result = orlo.queries.count_releases(**self.EXCLUSIVE_ARGS).all()
        self.assertEqual(0, result[0][0])


class CountReleasesStatus(TestCountReleases):
    """
    Test count_releases when filtering on status

    Note that this is a special case, as whether we consider a release
    successful or failed depends on the _combination_ of the package statuses.

    Will also run parent class tests with arguments below
    """
    INCLUSIVE_ARGS = {'status': 'SUCCESSFUL'}
    EXCLUSIVE_ARGS = {'status': 'FAILED'}

    def test_count_releases_excludes_failed(self):
        """
        Test that count_releases only returns successful releases

        By adding a failed one
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

        result = orlo.queries.count_releases(**self.INCLUSIVE_ARGS).all()
        self.assertEqual(3, result[0][0])

    def test_count_releases_invalid_status(self):
        """
        Test that we raise OrloError when proving an invalid status

        As this is an enum it's more useful to raise an error than simply
        return a zero count
        """
        with self.assertRaises(orlo.exceptions.OrloError):
            query = orlo.queries.count_releases(status='BAD_STATUS_FOOBAR')
            query.all()

    def test_count_releases_in_progress(self):
        """
        Test that we correctly return the number of releases in progress
        """
        for _ in range(0, 3):
            # 3 complete, successful releases
            self._create_finished_release()

        # And a fourth with the packages still in progress
        rid = self._create_release()
        pid1 = self._create_package(rid)
        pid2 = self._create_package(rid)
        self._start_package(pid1)
        self._start_package(pid2)

        result = orlo.queries.count_releases(status='IN_PROGRESS').all()
        self.assertEqual(1, result[0][0])


class CountReleasesUser(TestCountReleases):
    """
    Test count_releases when filtering on user
    """
    INCLUSIVE_ARGS = {'user': 'testuser'}
    EXCLUSIVE_ARGS = {'user': 'bad_foo_user'}


class CountReleasesTeam(TestCountReleases):
    """
    Test count_releases when filtering on team
    """
    INCLUSIVE_ARGS = {'team': 'test team'}
    EXCLUSIVE_ARGS = {'team': 'bad team does not exist'}


class CountReleasesPackage(TestCountReleases):
    """
    Test count_releases when filtering on package
    """
    INCLUSIVE_ARGS = {'package': 'test-package'}
    EXCLUSIVE_ARGS = {'package': 'non-existent-package'}


class CountReleasesPlatform(TestCountReleases):
    """
    Test count_releases when filtering on platform
    """
    INCLUSIVE_ARGS = {'platform': 'test_platform'}
    EXCLUSIVE_ARGS = {'platform': 'non_existent_platform'}


class CountReleasesRollback(TestCountReleases):
    """
    Test count_releases when filtering on rollback

    The args are a little counterintuitive here, but True is the exclusive case
    because the parent class does not create releases with rollback set to True.
    """
    INCLUSIVE_ARGS = {'rollback': False}
    EXCLUSIVE_ARGS = {'rollback': True}

    def test_bad_rollback_param_raises_type_error(self):
        """
        Test that we get a TypeError when passing garbage to the rollback param
        """
        with self.assertRaises(TypeError):
            orlo.queries.count_releases(rollback='foo')

    def test_rollback_true(self):
        """
        Test that we correctly count rollback releases

        The parent class creates only non-rollback releases
        """
        for _ in range(0, 3):
            # 3 complete, non-rollback releases
            self._create_finished_release()

        # And a fourth with all packages rollbacks
        rid = self._create_release()
        self._create_package(rid, rollback=True)
        self._create_package(rid, rollback=True)

        result = orlo.queries.count_releases(rollback=True).all()
        self.assertEqual(1, result[0][0])

    def test_rollback_false(self):
        """
        Test that we exclude rollback releases when setting rollback = False
        """
        rid = self._create_release()
        self._create_package(rid, rollback=True)
        self._create_package(rid, rollback=False)

        result = orlo.queries.count_releases(rollback=False).all()
        self.assertEqual(0, result[0][0])

    def test_partial_rollback(self):
        """
        Test a release is still counted when some packages are not rollbacks
        """
        for _ in range(0, 3):
            # 3 complete, non-rollback releases
            self._create_finished_release()

        # And a fourth with one package rollback, one not
        rid = self._create_release()
        self._create_package(rid, rollback=True)
        self._create_package(rid, rollback=False)

        result = orlo.queries.count_releases(rollback=True).all()
        self.assertEqual(1, result[0][0])


class CountPackagesTest(OrloQueryTest):
    """
    Parent class for testing the CountPackages function

    By subclassing it and overriding ARGS, we can test different combinations
    of arguments with the same test code.

    INCLUSIVE_ARGS represents a set of arguments that will match the packages
    created (see the functions in OrloQueryTest for what those are)
    EXCLUSIVE_ARGS represents a set of arguments that will not match any
    packages created, i.e. should return a count of zero

    This parent class has tests that should be the same result no matter what
    the arguments (except the exclusive case which must always a count of zero
    so we define it here)
    """

    INCLUSIVE_ARGS = {}  # Args we are testing, result should include these
    EXCLUSIVE_ARGS = {'user': 'non-existent'}  # Args which result in zero

    def test_count_packages(self):
        """
        Test count_packages in the simplest case
        """
        self._create_finished_release()
        result = orlo.queries.count_packages(**self.INCLUSIVE_ARGS).all()
        self.assertEqual(1, result[0][0])

    def test_count_packages_length(self):
        """
        Test that the function returns the correct number of items
        """
        for _ in range(0, 3):
            self._create_finished_release()
        # Should still only return one result (a count)
        result = orlo.queries.count_packages(**self.INCLUSIVE_ARGS).all()
        self.assertEqual(1, len(result))

    def test_count_packages_inclusive(self):
        """
        Test count_packages returns count of one filtering on INCLUSIVE_ARGS
        """
        self._create_finished_release()
        result = orlo.queries.count_packages(**self.INCLUSIVE_ARGS).all()
        self.assertEqual(1, result[0][0])

    def test_count_packages_exclusive(self):
        """
        Test count_packages returns a count of zero filtering on EXCLUSIVE_ARGS
        """
        self._create_finished_release()
        result = orlo.queries.count_packages(**self.EXCLUSIVE_ARGS).all()
        self.assertEqual(0, result[0][0])


class CountPackagesStatus(CountPackagesTest):
    """
    Test count_packages when filtering on status

    Note that this is a special case, as whether we consider a release
    successful or failed depends on the _combination_ of the package statuses.

    Will also run parent class tests with arguments below
    """
    INCLUSIVE_ARGS = {'status': 'SUCCESSFUL'}
    EXCLUSIVE_ARGS = {'status': 'FAILED'}


class CountPackagesUser(CountPackagesTest):
    """
    Test count_packages when filtering on user
    """
    INCLUSIVE_ARGS = {'user': 'testuser'}
    EXCLUSIVE_ARGS = {'user': 'bad_foo_user'}


class CountPackagesTeam(CountPackagesTest):
    """
    Test count_packages when filtering on team
    """
    INCLUSIVE_ARGS = {'team': 'test team'}
    EXCLUSIVE_ARGS = {'team': 'bad team does not exist'}


class CountPackagesPlatform(CountPackagesTest):
    """
    Test count_packages when filtering on platform
    """
    INCLUSIVE_ARGS = {'platform': 'test_platform'}
    EXCLUSIVE_ARGS = {'platform': 'non_existent_platform'}


class CountPackagesRollback(CountPackagesTest):
    """
    Test count_packages when filtering on rollback
    """
    INCLUSIVE_ARGS = {'rollback': False}
    EXCLUSIVE_ARGS = {'rollback': True}

    def test_rollback_true(self):
        """
        Test count_packages returns a count of one filtering on INCLUSIVE_ARGS
        """
        rid = self._create_release()
        self._create_package(rid, rollback=True)
        self._create_package(rid, rollback=True)

        result = orlo.queries.count_packages(rollback=True).all()
        self.assertEqual(2, result[0][0])

    def test_rollback_false(self):
        """
        Test count_packages returns a count of one filtering on INCLUSIVE_ARGS
        """
        rid = self._create_release()
        self._create_package(rid, rollback=True)
        self._create_package(rid, rollback=False)

        result = orlo.queries.count_packages(rollback=False).all()
        self.assertEqual(1, result[0][0])


class ReleasesTest(OrloQueryTest):
    """
    Test the releases method
    """

    def test_releases_with_bad_limit(self):
        """
        Test releases raises InvalidUsage when limit is not an int
        """
        args = {
            'limit': 'bad_limit',
        }
        with self.assertRaises(orlo.exceptions.InvalidUsage):
            orlo.queries.releases(**args)

    def test_releases_with_bad_offset(self):
        """
        Test releases raises InvalidUsage when offset is not an int
        """
        args = {
            'offset': 'bad_offset',
        }
        with self.assertRaises(orlo.exceptions.InvalidUsage):
            orlo.queries.releases(**args)


class GetPackageTest(OrloQueryTest):
    """
    Test the packages method
    """

    def test_get_package_returns_query(self):
        """
        Test that we return a Query object
        """
        result = orlo.queries.get_package('foo')
        self.assertIsInstance(result, sqlalchemy.orm.query.Query)

    def test_get_package_works(self):
        """
        Test that the query will give us the right package
        """
        rid = self._create_release()
        pid = self._create_package(rid, rollback=False)
        result = orlo.queries.get_package(pid).all()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, pid)


class PackagesTests(OrloQueryTest):
    """
    Test the queries.packages method
    """
    def test_packages_returns_query(self):
        """
        Test that
        :return:
        """
        result = orlo.queries.packages()
        self.assertIsInstance(result, sqlalchemy.orm.query.Query)

    def test_packages_works(self):
        """
        Test that query returned by get_package works
        """
        rid = self._create_release()
        pid = self._create_package(rid, rollback=False)
        result = orlo.queries.packages().all()
        self.assertEqual(result[0].id, pid)
