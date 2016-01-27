from __future__ import print_function
from orlo.queries import apply_filters, filter_release_rollback, filter_release_status
from orlo import app
from orlo.orm import db, Release, Platform, Package, release_platform
from orlo.exceptions import OrloError, InvalidUsage
from collections import OrderedDict

__author__ = 'alforbes'

"""
Functions related to building statistics
"""


def releases_by_time(unit, summarize_by_unit=False, **kwargs):
    """
    Return stats by time from the given arguments

    Functions in this file usually return a query object, but here we are
    returning the result, as there are several queries in play.

    :param summarize_by_unit: Passed to add_release_by_time_to_dict()
    :param unit: Passed to add_release_by_time_to_dict()
    """

    root_query = db.session.query(Release.id, Release.stime).join(Package)
    root_query = apply_filters(root_query, kwargs)

    # Build queries for the individual stats
    q_normal_successful = filter_release_status(
            filter_release_rollback(root_query, rollback=False), 'SUCCESSFUL'
    )
    q_normal_failed = filter_release_status(
            filter_release_rollback(root_query, rollback=False), 'FAILED'
    )
    q_rollback_successful = filter_release_status(
            filter_release_rollback(root_query, rollback=True), 'SUCCESSFUL'
    )
    q_rollback_failed = filter_release_status(
            filter_release_rollback(root_query, rollback=True), 'FAILED'
    )

    output_dict = OrderedDict()

    add_releases_by_time_to_dict(
            q_normal_successful, output_dict, ('normal', 'successful'), unit, summarize_by_unit)
    add_releases_by_time_to_dict(
            q_normal_failed, output_dict, ('normal', 'failed'), unit, summarize_by_unit)
    add_releases_by_time_to_dict(
            q_rollback_successful, output_dict, ('rollback', 'successful'), unit,
            summarize_by_unit)
    add_releases_by_time_to_dict(
            q_rollback_failed, output_dict, ('rollback', 'failed'), unit, summarize_by_unit)

    return output_dict


def package_by_time(unit, summarize_by_unit=False, **kwargs):
    """
    Count packages from the filters given

    Functions in this file usually return a query object, but here we are
    returning the result, as there are several queries in play.

    :param summarize_by_unit: Passed to add_release_by_time_to_dict()
    :param unit: Passed to add_release_by_time_to_dict()
    """

    root_query = db.session.query(Package.id, Package.stime).join(Release)
    root_query = apply_filters(root_query, kwargs)

    # Build queries for the individual stats
    q_normal_successful = filter_release_status(
            filter_release_rollback(root_query, rollback=False), 'SUCCESSFUL'
    )
    q_normal_failed = filter_release_status(
            filter_release_rollback(root_query, rollback=False), 'FAILED'
    )
    q_rollback_successful = filter_release_status(
            filter_release_rollback(root_query, rollback=True), 'SUCCESSFUL'
    )
    q_rollback_failed = filter_release_status(
            filter_release_rollback(root_query, rollback=True), 'FAILED'
    )

    output_dict = OrderedDict()

    add_releases_by_time_to_dict(
            q_normal_successful, output_dict, ('normal', 'successful'), unit, summarize_by_unit)
    add_releases_by_time_to_dict(
            q_normal_failed, output_dict, ('normal', 'failed'), unit, summarize_by_unit)
    add_releases_by_time_to_dict(
            q_rollback_successful, output_dict, ('rollback', 'successful'), unit,
            summarize_by_unit)
    add_releases_by_time_to_dict(
            q_rollback_failed, output_dict, ('rollback', 'failed'), unit, summarize_by_unit)

    return output_dict


# TODO add stats_user_time and stats_team_time
# or generalise a stats_time function


def add_releases_by_time_to_dict(query, releases_dict, t_category, unit='month',
                                 summarize_by_unit=False):
    """
    Take a query and add each of its releases to a dictionary, broken down by time

    :param dict releases_dict: Dict to add to
    :param tuple t_category: tuple of headings, i.e. (<normal|rollback>, <successful|failed>)
    :param query query: Query object to retrieve releases from
    :param string unit: Can be 'iso', 'hour', 'day', 'week', 'month', 'year',
    :param boolean summarize_by_unit: Only break down releases by the given unit, i.e. only one
        layer deep. For example, if "year" is the unit, we group all releases under the year
        and do not add month etc underneath.
    :return:

    **Note**: this can also be use for packages
    """

    for release in query:
        if summarize_by_unit:
            tree_args = [str(getattr(release.stime, unit))]
        else:
            if unit == 'year':
                tree_args = [str(release.stime.year)]
            elif unit == 'month':
                tree_args = [str(release.stime.year), str(release.stime.month)]
            elif unit == 'week':
                # First two args of isocalendar(), year and week
                tree_args = [str(i) for i in release.stime.isocalendar()][0:2]
            elif unit == 'iso':
                tree_args = [str(i) for i in release.stime.isocalendar()]
            elif unit == 'day':
                tree_args = [str(release.stime.year), str(release.stime.month),
                             str(release.stime.day)]
            elif unit == 'hour':
                tree_args = [str(release.stime.year), str(release.stime.month),
                             str(release.stime.day), str(release.stime.hour)]
            else:
                raise InvalidUsage(
                        'Invalid unit "{}" specified for release breakdown'.format(unit))
        # Append categories
        tree_args += t_category
        append_tree_recursive(releases_dict, tree_args[0], tree_args)


def append_tree_recursive(tree, parent, nodes):
    """
    Recursively place the nodes under each other

    :param dict tree: The dictionary we are operating on
    :param parent: The parent for this node
    :param nodes: The list of nodes
    :return:
    """
    app.logger.debug('Called recursive function with args:\n{}, {}, {}'.format(
            str(tree), str(parent), str(nodes)))
    try:
        # Get the child, one after the parent
        child = nodes[nodes.index(parent) + 1]
    except IndexError:
        # Must be at end
        if parent in tree:
            tree[parent] += 1
        else:
            tree[parent] = 1
        return tree

    # Otherwise recurse again
    if parent not in tree:
        tree[parent] = {}
    # Child becomes the parent
    append_tree_recursive(tree[parent], child, nodes)
