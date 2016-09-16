from __future__ import print_function
from datetime import date, timedelta, datetime

from orlo.util import append_or_create_platforms

from test_orm import OrloDbTest
from orlo.orm import db, Release, Package

__author__ = 'alforbes'

"""
This tests the stats functions by creating a known dataset,
making the results predictable
"""


def date_range(start, end):
    # Courtesy of http://stackoverflow.com/questions/1060279
    for n in range(int((end - start).days)):
        yield start + timedelta(n)


class TestStatsEmpirical(OrloDbTest):
    """
    Test release stats by creating a known data set

    Changing the dates or number of releases may impact tests
    """

    # Create releases for two days which span a year
    start_date = datetime(2015, 12, 31)
    end_date = datetime(2016, 1, 2)

    # Which means results for 2015-12-31 and 2016-01-01 should match below:
    normal_successful_per_day = 2
    normal_failed_per_day = 1
    rollback_successful_per_day = 1
    rollback_failed_per_day = 1

    package_list = ['p1', 'p2']

    time_cursor = start_date

    def setUp(self):
        self.releases = 0
        super(OrloDbTest, self).setUp()

        for day in date_range(self.start_date, self.end_date):
            if day.weekday() > 5:
                # weekend! don't release
                continue

            # starting at 9am...
            self.time_cursor = day + timedelta(hours=9)

            # do $per_day releases...
            for i in range(0, self.normal_successful_per_day):
                self.create_release(True, True)
            for i in range(0, self.normal_failed_per_day):
                self.create_release(True, False)
            for i in range(0, self.rollback_successful_per_day):
                self.create_release(False, True)
            for i in range(0, self.rollback_failed_per_day):
                self.create_release(False, False)

            db.session.commit()
        # print("Total releases created: {}".format(self.releases))

    def create_release(self, normal, successful, user='test_user', team='test_team',
                       platform='test_platform'):
        release = Release(
                platforms=append_or_create_platforms([platform]),
                user=user,
                team=team,
                # references=list_to_string(['test_reference'])
        )
        release.stime = self.time_cursor
        db.session.add(release)

        for package in self.package_list:
            package = Package(
                release_id=release.id,
                name=package,
                version='0.0.0'
            )
            # which take 10 mins each...
            package.stime = self.time_cursor
            package.ftime = self.time_cursor = self.time_cursor + timedelta(minutes=10)
            if normal:
                package.rollback = False
            else:
                package.rollback = True
            if successful:
                package.status = 'SUCCESSFUL'
            else:
                package.status = 'FAILED'
            db.session.add(package)

        release.ftime = self.time_cursor
        release.duration = release.ftime - release.stime
        self.releases += 1

    def test_stats(self):
        """
        Test our data against /stats
        """
        response = self.client.get('/stats').json
        total = response['global']['releases']['total']
        self.assertEqual(total['successful'] + total['failed'],  self.releases)

    def test_stats_user(self):
        """
        Test /stats/user with data
        """
        # Add a release with a different user
        self.create_release(False, False, user='bad_user')

        response = self.client.get('/stats/user/test_user').json
        total = response['test_user']['releases']['total']
        self.assertEqual(total['successful'] + total['failed'], self.releases - 1)

    def test_stats_team(self):
        """
        Test /stats/team with data
        """
        # Add a release with a different team
        self.create_release(False, False, team='bad_team')

        response = self.client.get('/stats/team/test_team').json
        total = response['test_team']['releases']['total']
        self.assertEqual(total['successful'] + total['failed'], self.releases - 1)

    def test_stats_platform(self):
        """
        Test /stats/platform with data
        """
        # Add a release with a different team
        self.create_release(False, False, platform='bad_platform')

        response = self.client.get('/stats/platform/test_platform').json
        total = response['test_platform']['releases']['total']
        self.assertEqual(total['successful'] + total['failed'], self.releases - 1)

    def test_stats_package(self):
        """
        Test /stats/package with data
        """
        # All packages are in every release here, could be better tested
        response = self.client.get('/stats/package/p1').json
        total = response['p1']['releases']['total']
        self.assertEqual(total['successful'] + total['failed'], self.releases)

    def test_stats_by_date_release(self):
        """
        Tests /stats/by_date/release
        """
        s_year = self.start_date.year
        s_month = self.start_date.month
        response = self.client.get('/stats/by_date/release')

        self.assertEqual(
                response.json[str(s_year)][str(s_month)]['normal']['successful'],
                self.normal_successful_per_day,
        )
        self.assertEqual(
                response.json[str(s_year)][str(s_month)]['normal']['successful'],
                self.normal_successful_per_day,
        )
        self.assertEqual(
                response.json[str(s_year + 1)]['1']['rollback']['failed'],
                self.rollback_failed_per_day
        )

    def test_stats_by_date_package(self):
        """
        Tests /stats/by_date/package
        """
        s_year = self.start_date.year
        s_month = self.start_date.month
        response = self.client.get('/stats/by_date/package')

        # Assumes p1 is in every release
        self.assertEqual(
            response.json[str(s_year)][str(s_month)]['p1']['normal']['successful'],
            self.normal_successful_per_day,
        )
        self.assertEqual(
            response.json[str(s_year)][str(s_month)]['p2']['normal']['successful'],
            self.normal_successful_per_day,
        )
        self.assertEqual(
            response.json[str(s_year + 1)]['1']['p1']['rollback']['failed'],
            self.rollback_failed_per_day
        )

    def test_stats_by_date_release_with_unit_day(self):
        """
        Tests /stats/by_date/release
        """
        s_year = self.start_date.year
        s_month = self.start_date.month
        response = self.client.get('/stats/by_date/release?unit=day')

        self.assertEqual(
                response.json[str(s_year)][str(s_month)]['31']['normal']['successful'],
                self.normal_successful_per_day,
        )
        self.assertEqual(
                response.json[str(s_year)][str(s_month)]['31']['normal']['successful'],
                self.normal_successful_per_day,
        )
        self.assertEqual(
                response.json[str(s_year + 1)]['1']['1']['rollback']['failed'],
                self.rollback_failed_per_day
        )

    def test_stats_by_date_package_with_unit_day(self):
        """
        Tests /stats/by_date/package
        """
        s_year = self.start_date.year
        s_month = self.start_date.month
        response = self.client.get('/stats/by_date/package?unit=day')

        # Assumes p1 is in every release
        self.assertEqual(
                response.json[str(s_year)][str(s_month)]['31']['p1']['normal']['successful'],
                self.normal_successful_per_day,
        )
        self.assertEqual(
                response.json[str(s_year)][str(s_month)]['31']['p2']['normal']['successful'],
                self.normal_successful_per_day,
        )
        self.assertEqual(
                response.json[str(s_year + 1)]['1']['1']['p1']['rollback']['failed'],
                self.rollback_failed_per_day
        )
