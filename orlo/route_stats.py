import arrow
from flask import request, jsonify

from orlo import stats
from orlo import app
from orlo.exceptions import InvalidUsage
import orlo.queries as queries

__author__ = 'alforbes'

"""
#TODO The stats_ functions in this file are very similar, which means they should probably be
broken down a different way
"""


def build_stats_dict(field, value_list, platform=None, stime=None, ftime=None):
    """
    Build a dictionary of our stats

    :param field: The field we are build stats for, i.e. user, package, team or platform
    :param value_list: The list of values for the field
    :param platform: Filter by platform
    :param datetime ftime: Passed to count_releases
    :param datetime stime: Passed to count_releases
    :return:
    """

    app.logger.debug("Entered build_stats_dict")

    d_stats = {}
    count_releases_args = {
        'stime': stime,
        'ftime': ftime,
        'platform': platform,  # note, platform can also be the field in the loop below
    }

    for field_value in value_list:
        app.logger.debug("Getting stats for {} {}".format(field, field_value))

        count_releases_args[field] = field_value  # e.g. need to pass user=username

        c_total_successful = queries.count_releases(
                status='SUCCESSFUL', **count_releases_args).all()[0][0]
        c_total_failed = queries.count_releases(
                status='FAILED', **count_releases_args).all()[0][0]
        c_normal_successful = queries.count_releases(
                rollback=False, status='SUCCESSFUL', **count_releases_args).all()[0][0]
        c_normal_failed = queries.count_releases(
                rollback=False, status='FAILED', **count_releases_args).all()[0][0]
        c_rollback_successful = queries.count_releases(
                rollback=True, status='SUCCESSFUL', **count_releases_args).all()[0][0]
        c_rollback_failed = queries.count_releases(
                rollback=True, status='FAILED', **count_releases_args).all()[0][0]

        d_stats[field_value] = {
            'releases': {
                'normal': {
                    'successful': c_normal_successful,
                    'failed': c_normal_failed,
                },
                'rollback': {
                    'successful': c_rollback_successful,
                    'failed': c_rollback_failed,
                },
                'total': {
                    'successful': c_total_successful,
                    'failed': c_total_failed,
                },
            }
        }

    return d_stats


def build_all_stats_dict(stime=None, ftime=None):
    """
    Build a dictionary of our stats

    :param datetime ftime: Passed to count_releases
    :param datetime stime: Passed to count_releases

    :return:
    """

    app.logger.debug("Entered build_all_stats_dict")

    count_releases_args = {
        'stime': stime,
        'ftime': ftime,
    }

    app.logger.debug("Getting global stats")

    c_total_successful = queries.count_releases(
            status='SUCCESSFUL', **count_releases_args).all()[0][0]
    c_total_failed = queries.count_releases(
            status='FAILED', **count_releases_args).all()[0][0]
    c_normal_successful = queries.count_releases(
            rollback=False, status='SUCCESSFUL', **count_releases_args).all()[0][0]
    c_normal_failed = queries.count_releases(
            rollback=False, status='FAILED', **count_releases_args).all()[0][0]
    c_rollback_successful = queries.count_releases(
            rollback=True, status='SUCCESSFUL', **count_releases_args).all()[0][0]
    c_rollback_failed = queries.count_releases(
            rollback=True, status='FAILED', **count_releases_args).all()[0][0]

    d_stats = {
        'global': {
            'releases': {
                'normal': {
                    'successful': c_normal_successful,
                    'failed': c_normal_failed,
                },
                'rollback': {
                    'successful': c_rollback_successful,
                    'failed': c_rollback_failed,
                },
                'total': {
                    'successful': c_total_successful,
                    'failed': c_total_failed,
                },
            }
        }
    }

    return d_stats


@app.route('/stats')
def stats_():
    """
    Return dictionary of global stats

    :query string stime: The lower bound of the time period to filter on
    :query string ftime: The upper bound of the time period to filter on
    """
    s_stime = request.args.get('stime')
    s_ftime = request.args.get('ftime')

    stime, ftime = None, None
    try:
        if s_stime:
            stime = arrow.get(s_stime)
        if s_ftime:
            ftime = arrow.get(s_ftime)
    except RuntimeError:  # super-class to arrow's ParserError, which is not importable
        raise InvalidUsage("A badly formatted datetime string was given")

    app.logger.debug("Building all_stats dict")
    all_stats = build_all_stats_dict(stime=stime, ftime=ftime)

    return jsonify(all_stats)


@app.route('/stats/user')
@app.route('/stats/user/<username>')
def stats_user(username=None):
    """
    Return a dictionary of statistics for a username (optional), or all users

    :param string username: The username to provide u_stats for
    :query string stime: The lower bound of the time period to filter on
    :query string ftime: The upper bound of the time period to filter on

    stime and ftime both filter on the release start time.
    Note that standard orlo API filters can be used here as well, not just stime/ftime
    """
    s_stime = request.args.get('stime')
    s_ftime = request.args.get('ftime')

    stime, ftime = None, None
    try:
        if s_stime:
            stime = arrow.get(s_stime)
        if s_ftime:
            ftime = arrow.get(s_ftime)
    except RuntimeError:  # super-class to arrows ParserError, which is not importable
        raise InvalidUsage("A badly formatted datetime string was given")

    if username:
        user_list = [username]
    else:
        app.logger.debug("Fetching user list")
        user_result = queries.user_list().all()
        # Flatten query result
        user_list = [u[0] for u in user_result]

    app.logger.debug("Building stats dict")
    user_stats = build_stats_dict('user', user_list, stime=stime, ftime=ftime)

    return jsonify(user_stats)


@app.route('/stats/team')
@app.route('/stats/team/<team>')
def stats_team(team=None):
    """
    Return a dictionary of statistics for a team (optional), or all teams

    :param string team: The team name to provide t_stats for
    :query string stime: The lower bound of the time period to filter on
    :query string ftime: The upper bound of the time period to filter on

    stime and ftime both filter on the release start time.
    """
    s_stime = request.args.get('stime')
    s_ftime = request.args.get('ftime')

    stime, ftime = None, None
    try:
        if s_stime:
            stime = arrow.get(s_stime)
        if s_ftime:
            ftime = arrow.get(s_ftime)
    except RuntimeError:  # super-class to arrows ParserError, which is not importable
        raise InvalidUsage("A badly formatted datetime string was given")

    if team:
        team_list = [team]
    else:
        team_result = queries.team_list().all()
        # Flatten query result
        team_list = [u[0] for u in team_result]

    team_stats = build_stats_dict('team', team_list, stime=stime, ftime=ftime)

    return jsonify(team_stats)


@app.route('/stats/platform')
@app.route('/stats/platform/<platform>')
def stats_platform(platform=None):
    """
    Return a dictionary of statistics for a platform name (optional), or all platforms

    :param string platform: The platform name to provide stats for
    :query string stime: The lower bound of the time period to filter on
    :query string ftime: The upper bound of the time period to filter on

    stime and ftime both filter on the release start time.
    Note that standard orlo API filters can be used here as well, not just stime/ftime
    """
    s_stime = request.args.get('stime')
    s_ftime = request.args.get('ftime')

    try:
        stime, ftime = None, None
        if s_stime:
            stime = arrow.get(s_stime)
        if s_ftime:
            ftime = arrow.get(s_ftime)
    except RuntimeError:  # super-class to arrows ParserError, which is not importable
        raise InvalidUsage("A badly formatted datetime string was given")

    if platform:
        platform_list = [platform]
    else:
        platform_result = queries.platform_list().all()
        # Flatten query result
        platform_list = [u[0] for u in platform_result]

    platform_stats = build_stats_dict('platform', platform_list, stime=stime, ftime=ftime)

    return jsonify(platform_stats)


@app.route('/stats/package')
@app.route('/stats/package/<package>')
def stats_package(package=None):
    """
    Return a dictionary of statistics for a package name (optional), or all packages

    :param string package: The package name to provide p_stats for
    :query string stime: The lower bound of the time period to filter on
    :query string ftime: The upper bound of the time period to filter on

    stime and ftime both filter on the release start time.
    Note that standard orlo API filters can be used here as well, not just stime/ftime
    """
    s_stime = request.args.get('stime')
    s_ftime = request.args.get('ftime')

    stime, ftime = None, None
    try:
        if s_stime:
            stime = arrow.get(s_stime)
        if s_ftime:
            ftime = arrow.get(s_ftime)
    except RuntimeError:  # super-class to arrows ParserError, which is not importable
        raise InvalidUsage("A badly formatted datetime string was given")

    if package:
        package_list = [package]
    else:
        package_result = queries.package_list().all()
        # Flatten query result
        package_list = [u[0] for u in package_result]

    package_stats = build_stats_dict('package', package_list, stime=stime, ftime=ftime)

    return jsonify(package_stats)


@app.route('/stats/by_date/<subject>')
def stats_by_date(subject='release'):
    """
    Return stats by date

    :param subject: Release or Package (default: release)
    :query string unit: Unit to group by, i.e. year, month, week, day, hour
    :query boolean summarize_by_unit: Don't build hierarchy, just summarize by the unit
    :return:

    This endpoint also allows filtering on the same fields as GET /releases, e.g stime_gt. See
    that endpoint for documentation.
    """

    # Get the filters into an args directory, if they are set
    filters = dict((k, v) for k, v in request.args.items())
    unit = filters.pop('unit', 'month')

    if filters.pop('summarize_by_unit', False):
        summarize_by_unit = True
    else:
        summarize_by_unit = False

    # Returns releases and their time by rollback and status
    if subject == 'release':
        release_stats = stats.releases_by_time(unit, summarize_by_unit, **filters)
    elif subject == 'package':
        release_stats = stats.packages_by_time(unit, summarize_by_unit, **filters)
    else:
        raise InvalidUsage("subject must release or package, not '{}'".format())

    return jsonify(release_stats)


