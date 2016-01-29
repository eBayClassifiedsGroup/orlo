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

    :param summarize_by_unit: Passed to add_release_by_time_to_dict()
    :param unit: Passed to add_release_by_time_to_dict()
    """

    query = db.session.query(Release.id, Release.stime).join(Package).group_by(Release)
    query = apply_filters(query, kwargs)

    return get_dict_of_objects_by_time(query, unit, summarize_by_unit)


def packages_by_time(unit, summarize_by_unit=False, **kwargs):
    """
    Count packages by time from the filters given

    :param summarize_by_unit: Passed to add_release_by_time_to_dict()
    :param unit: Passed to add_release_by_time_to_dict()
    """

    query = db.session.query(Package.id, Package.name, Package.stime).join(Release)
    query = apply_filters(query, kwargs)

    return get_dict_of_objects_by_time(query, unit, summarize_by_unit)


# TODO add stats_user_time and stats_team_time
# or generalise a stats_time function


def get_dict_of_objects_by_time(query, unit, summarize_by_unit=False):
    """
    Build a dictionary which summarises the objects in the query given

    :param query:
    :param unit:
    :param summarize_by_unit:
    :return:
    """

    # Build queries for the individual stats
    q_normal_successful = filter_release_status(
            filter_release_rollback(query, rollback=False), 'SUCCESSFUL'
    )
    q_normal_failed = filter_release_status(
            filter_release_rollback(query, rollback=False), 'FAILED'
    )
    q_rollback_successful = filter_release_status(
            filter_release_rollback(query, rollback=True), 'SUCCESSFUL'
    )
    q_rollback_failed = filter_release_status(
            filter_release_rollback(query, rollback=True), 'FAILED'
    )

    output_dict = OrderedDict()

    add_objects_by_time_to_dict(
            q_normal_successful, output_dict, ('normal', 'successful'), unit, summarize_by_unit)
    add_objects_by_time_to_dict(
            q_normal_failed, output_dict, ('normal', 'failed'), unit, summarize_by_unit)
    add_objects_by_time_to_dict(
            q_rollback_successful, output_dict, ('rollback', 'successful'), unit,
            summarize_by_unit)
    add_objects_by_time_to_dict(
            q_rollback_failed, output_dict, ('rollback', 'failed'), unit, summarize_by_unit)

    return output_dict


def add_objects_by_time_to_dict(query, releases_dict, t_category, unit='month',
                                summarize_by_unit=False):
    """
    Take a query and add each of its objects to a dictionary, broken down by time

    If the query given has a 'name' column, that will be included in the dictionary path
    above the categories (t_category).

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
    app.logger.debug("Entered add_objects_by_time_to_dict")
    for object_ in query:
        if summarize_by_unit:
            tree_args = [str(getattr(object_.stime, unit))]
        else:
            if unit == 'year':
                tree_args = [str(object_.stime.year)]
            elif unit == 'month':
                tree_args = [str(object_.stime.year), str(object_.stime.month)]
            elif unit == 'week':
                # First two args of isocalendar(), year and week
                tree_args = [str(i) for i in object_.stime.isocalendar()][0:2]
            elif unit == 'iso':
                tree_args = [str(i) for i in object_.stime.isocalendar()]
            elif unit == 'day':
                tree_args = [str(object_.stime.year), str(object_.stime.month),
                             str(object_.stime.day)]
            elif unit == 'hour':
                tree_args = [str(object_.stime.year), str(object_.stime.month),
                             str(object_.stime.day), str(object_.stime.hour)]
            else:
                raise InvalidUsage(
                        'Invalid unit "{}" specified for release breakdown'.format(unit))
        if hasattr(object_, 'name'):
            #
            tree_args.append(object_.name)
        # Append categories
        tree_args += t_category
        append_tree_recursive(releases_dict, tree_args[0], tree_args)


def append_tree_recursive(tree, parent, nodes, node_index=0):
    """
    Recursively place the nodes under each other

    :param dict tree: The dictionary we are operating on
    :param parent: The parent for this node
    :param nodes: The list of nodes
    :param node_index: The position in the list list we are up to
    :return:
    """
    app.logger.debug('Called recursive function with args:\n{}, {}, {}'.format(
            str(tree), str(parent), str(nodes)))

    child_index = node_index + 1
    try:
        # Get the child, one after the parent
        child = nodes[child_index]
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
    append_tree_recursive(tree[parent], child, nodes, node_index=child_index)
