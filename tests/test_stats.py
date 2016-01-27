from __future__ import print_function, unicode_literals
import arrow
import orlo.queries
import orlo.exceptions
import orlo.stats
from tests.test_orm import OrloDbTest

__author__ = 'alforbes'


class ReleaseTimeTest(OrloDbTest):
    """
    Test stats.release_time
    """
    ARGS = {
        'stime_gt': arrow.utcnow().replace(hours=-1),
        'stime_lt': arrow.utcnow().replace(hours=+1)
    }

    def setUp(self):
        super(OrloDbTest, self).setUp()

        for r in range(0, 7):
            self._create_finished_release()

    def test_append_tree_recursive(self):
        """
        Test that append_tree_recursive returns a properly structured dictionary
        """
        tree = {}
        nodes = ['apple', 'orange']
        orlo.stats.append_tree_recursive(tree, nodes[0], nodes)
        self.assertEqual(tree, {'apple': {'orange': 1}})

    def test_append_tree_recursive_adds(self):
        """
        Test that append_tree_recursive correctly adds one when called on the same path
        """
        tree = {}
        nodes = ['apple', 'orange']
        orlo.stats.append_tree_recursive(tree, nodes[0], nodes)
        orlo.stats.append_tree_recursive(tree, nodes[0], nodes)
        self.assertEqual(tree, {'apple': {'orange': 2}})

    def test_release_time_month(self):
        """
        Test queries.add_releases_by_time_to_dict by month
        """
        result = orlo.stats.releases_by_time('month', **self.ARGS)
        year = str(arrow.utcnow().year)
        month = str(arrow.utcnow().month)
        self.assertEqual(7, result[year][month]['normal']['successful'])

    def test_release_time_week(self):
        """
        Test queries.add_releases_by_time_to_dict by week
        """
        result = orlo.stats.releases_by_time('week', **self.ARGS)
        year, week, day = arrow.utcnow().isocalendar()
        self.assertEqual(7, result[str(year)][str(week)]['normal']['successful'])

    def test_release_time_year(self):
        """
        Test queries.add_releases_by_time_to_dict by year
        """
        result = orlo.stats.releases_by_time('year', **self.ARGS)
        year = str(arrow.utcnow().year)
        self.assertEqual(7, result[str(year)]['normal']['successful'])

    def test_release_time_day(self):
        """
        Test queries.add_releases_by_time_to_dict by day
        """
        result = orlo.stats.releases_by_time('day', **self.ARGS)
        year = str(arrow.utcnow().year)
        month = str(arrow.utcnow().month)
        day = str(arrow.utcnow().day)
        self.assertEqual(
                7,
                result[year][month][day]['normal']['successful'],
        )

    def test_release_time_hour(self):
        """
        Test queries.add_releases_by_time_to_dict by hour
        """
        result = orlo.stats.releases_by_time('hour', **self.ARGS)
        year = str(arrow.utcnow().year)
        month = str(arrow.utcnow().month)
        day = str(arrow.utcnow().day)
        hour = str(arrow.utcnow().hour)
        self.assertEqual(
                7,
                result[year][month][day][hour]['normal']['successful'],
        )

    def test_release_time_with_only_this_unit(self):
        """
        Test queries.add_releases_by_time_to_dict with only_this_unit

        Should break down by only the unit given
        """
        result = orlo.stats.releases_by_time('hour', summarize_by_unit=True, **self.ARGS)
        hour = str(arrow.utcnow().hour)
        self.assertEqual(
                7,
                result[hour]['normal']['successful'],
        )

    def test_release_time_with_unit_day(self):
        pass
