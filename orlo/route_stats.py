from __future__ import print_function
from flask import request, jsonify
from orlo import app
from orlo.orm import db, Release, Package, Platform, release_platform
from orlo.util import apply_filters
from orlo.queries import user_summary

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
        user_list = [u for u, c in user_summary()]

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


@app.route('/stats/team')
@app.route('/stats/team/<teamname>')
def stats_team(teamname=None):
    """
    Return a dictionary of statistics for teams

    :param string teamname: The team name to report on, otherwise all teams are returned
    """


@app.route('/')
def stats_platform(platformname=None):
    """
    Return a dictionary of statistics for platforms

    :param string platformname:
    """