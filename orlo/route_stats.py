from __future__ import print_function
import arrow
from flask import request, jsonify
from orlo import app
from orlo.orm import db, Release, Package, Platform, release_platform
from orlo.util import apply_filters
import orlo.queries as queries

__author__ = 'alforbes'


@app.route('/stats')
def stats():
    msg = 'This is the orlo stats endpoint'
    return jsonify(message=msg), 200


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
    if s_stime:
        stime = arrow.get(s_stime)
    if s_ftime:
        ftime = arrow.get(s_ftime)

    if username:
        user_list = [username]
    else:
        user_result = queries.user_list().all()
        # Flatten query result
        user_list = [u[0] for u in user_result]

    u_stats = {}
    for user in user_list:
        c_total_successful = queries.count_releases(
                user=user, stime=stime, ftime=ftime, status='SUCCESSFUL').all()[0][0]
        c_total_failed = queries.count_releases(
                user=user, stime=stime, ftime=ftime, status='FAILED').all()[0][0]
        c_normal_successful = queries.count_releases(
                user=user, stime=stime, ftime=ftime, rollback=False,
                status='SUCCESSFUL').all()[0][0]
        c_normal_failed = queries.count_releases(
                user=user, stime=stime, ftime=ftime, rollback=False,
                status='FAILED').all()[0][0]
        c_rollback_successful = queries.count_releases(
                user=user, stime=stime, ftime=ftime, rollback=True,
                status='SUCCESSFUL').all()[0][0]
        c_rollback_failed = queries.count_releases(
                user=user, stime=stime, ftime=ftime, rollback=True,
                status='FAILED').all()[0][0]

        u_stats[user] = {
            'releases': {
                'total_successful': c_total_successful,
                'total_failed': c_total_failed,
                'normal_successful': c_normal_successful,
                'normal_failed': c_normal_failed,
                'rollback_successful': c_rollback_successful,
                'rollback_failed': c_rollback_failed,
            }
        }

    return jsonify(u_stats)


@app.route('/stats/team')
@app.route('/stats/team/<team>')
def stats_team(team=None):
    """
    Return a dictionary of statistics for a team (optional), or all teams

    :param string team: The team name to provide t_stats for
    :query string stime: The lower bound of the time period to filter on
    :query string ftime: The upper bound of the time period to filter on

    stime and ftime both filter on the release start time.
    Note that standard orlo API filters can be used here as well, not just stime/ftime
    """
    s_stime = request.args.get('stime')
    s_ftime = request.args.get('ftime')

    stime, ftime = None, None
    if s_stime:
        stime = arrow.get(s_stime)
    if s_ftime:
        ftime = arrow.get(s_ftime)

    if team:
        team_list = [team]
    else:
        team_result = queries.team_list().all()
        # Flatten query result
        team_list = [u[0] for u in team_result]

    t_stats = {}
    for team in team_list:
        c_total_successful = queries.count_releases(
                team=team, stime=stime, ftime=ftime, status='SUCCESSFUL').all()[0][0]
        c_total_failed = queries.count_releases(
                team=team, stime=stime, ftime=ftime, status='FAILED').all()[0][0]
        c_normal_successful = queries.count_releases(
                team=team, stime=stime, ftime=ftime, rollback=False,
                status='SUCCESSFUL').all()[0][0]
        c_normal_failed = queries.count_releases(
                team=team, stime=stime, ftime=ftime, rollback=False,
                status='FAILED').all()[0][0]
        c_rollback_successful = queries.count_releases(
                team=team, stime=stime, ftime=ftime, rollback=True,
                status='SUCCESSFUL').all()[0][0]
        c_rollback_failed = queries.count_releases(
                team=team, stime=stime, ftime=ftime, rollback=True,
                status='FAILED').all()[0][0]

        t_stats[team] = {
            'releases': {
                'total_successful': c_total_successful,
                'total_failed': c_total_failed,
                'normal_successful': c_normal_successful,
                'normal_failed': c_normal_failed,
                'rollback_successful': c_rollback_successful,
                'rollback_failed': c_rollback_failed,
            }
        }

    return jsonify(t_stats)


@app.route('/stats/platform')
@app.route('/stats/platform/<platform>')
def stats_platform(platform=None):
    """
    Return a dictionary of statistics for a platformname (optional), or all platforms

    :param string platform: The platform name to provide p_stats for
    :query string stime: The lower bound of the time period to filter on
    :query string ftime: The upper bound of the time period to filter on

    stime and ftime both filter on the release start time.
    Note that standard orlo API filters can be used here as well, not just stime/ftime
    """
    s_stime = request.args.get('stime')
    s_ftime = request.args.get('ftime')

    stime, ftime = None, None
    if s_stime:
        stime = arrow.get(s_stime)
    if s_ftime:
        ftime = arrow.get(s_ftime)

    if platform:
        platform_list = [platform]
    else:
        platform_result = queries.platform_list().all()
        # Flatten query result
        platform_list = [u[0] for u in platform_result]

    p_stats = {}
    for platform in platform_list:
        c_total_successful = queries.count_releases(
                platform=platform, stime=stime, ftime=ftime, status='SUCCESSFUL').all()[0][0]
        c_total_failed = queries.count_releases(
                platform=platform, stime=stime, ftime=ftime, status='FAILED').all()[0][0]
        c_normal_successful = queries.count_releases(
                platform=platform, stime=stime, ftime=ftime, rollback=False,
                status='SUCCESSFUL').all()[0][0]
        c_normal_failed = queries.count_releases(
                platform=platform, stime=stime, ftime=ftime, rollback=False,
                status='FAILED').all()[0][0]
        c_rollback_successful = queries.count_releases(
                platform=platform, stime=stime, ftime=ftime, rollback=True,
                status='SUCCESSFUL').all()[0][0]
        c_rollback_failed = queries.count_releases(
                platform=platform, stime=stime, ftime=ftime, rollback=True,
                status='FAILED').all()[0][0]

        p_stats[platform] = {
            'releases': {
                'total_successful': c_total_successful,
                'total_failed': c_total_failed,
                'normal_successful': c_normal_successful,
                'normal_failed': c_normal_failed,
                'rollback_successful': c_rollback_successful,
                'rollback_failed': c_rollback_failed,
            }
        }

    return jsonify(p_stats)
