from __future__ import print_function
from flask import request, jsonify
from orlo import app
from orlo.orm import db, Release, Package, Platform, release_platform
from orlo.util import apply_filters

__author__ = 'alforbes'


@app.route('/stats/user')
@app.route('/stats/user/<username>')
def stats_user(username=None):
    """
    Return a dictionary of statistics for a username (optional), or all users

    :param string username: The username to provide stats for
    :query string stime: The lower bound of the time period to filter on
    :query string ftime: The upper bound of the time period to filter on

    stime and ftime both filter on the release start time.
    Note that standard orlo API filters can be used here as well, not just stime/ftime
    """

    if username:
        user_list = [username]
    else:
        user_list = [u for u, c in get_summary_users()]

    if any(field.startswith('package_') for field in request.args.keys()):
        main_query = db.session.query(Release).join(Package)
    else:
        # No need to join on package if none of our params need it
        main_query = db.session.query(Release)

    if username:
        main_query = main_query.filter(Release.user == username)

    # Apply the orlo API filters from request.args
    main_query = apply_filters(main_query, request.args)

    sub_query = db.session.query()


@app.route('/info/users', methods=['GET'])
@app.route('/info/users/<platform>', methods=['GET'])
def info_users(platform=None):
    """
    Return a dictionary of users optionally filtering by platform

    :param platform:
    """
    users = get_summary_users(platform)
    d = {}
    for user, count in users:
        d[user] = {'releases': count}

    return jsonify(d), 200


@app.route('/info/platforms', methods=['GET'])
def info_platforms():
    """
    Return a summary of the platforms
    """
    d = {}

    for platform, count in get_summary_platforms():
        d[platform] = {'releases': count}
    return jsonify(d), 200


def get_releases_rollback(releases):
    """
    Return the number of rollback releases in this dict

    Note that a rollback release is defined as a release that has at least one rollback.
    Generally speaking, it is recommended to constrain releases to either rolling forward or back,
    and not both.

    :param releases: Releases dictionary as returned by query.all()
    :return: Int
    """

    c = 0
    for release in releases:
        for p in release.packages:
            if p.rollback:
                # Break on the first rollback encountered
                c += 1
                break
    return c


def get_successful_releases(platform=None):
    """
    Return the number of successful releases

    Note that a "successful" release is defined as a release where all packages are recorded as
    successful

    :return: Int
    """

    query = db.session.query(Release.id, db.func.count(Package.id))\
        .join(Package)

    if platform:
        query = query.filter(Release.platforms.any(Platform.name == platform))

    query = query.filter(~Release.packages.any(
            db.or_(Package.status != "SUCCESSFUL"))
        )\
        .group_by(Release.id)

    return query.all()


def get_summary_users(platform=None):
    """
    Find all users that have performed releases

    :param platform: Platform to filter on
    :return: Query result [('user', release_count)]
    """

    query = db.session.query(Release.user, db.func.count(Release.user))
    if platform:
        query = query.filter(Release.platforms.any(Platform.name == platform))

    return query.group_by(Release.user).all()


def get_summary_platforms():
    """
    Return a summary of the known platforms

    :return: Query result [('platform'), release_count]
    """

    query = db.session.query(
        Platform.name, db.func.count(Platform.id))\
        .join(release_platform)\
        .group_by(Platform.name)

    return query.all()
