from __future__ import print_function
from flask import request, jsonify
from orlo import app
from orlo.orm import db, Release, Package, Platform, release_platform
from orlo.util import apply_filters
from orlo.queries import user_summary, platform_summary

__author__ = 'alforbes'


@app.route('/info/users', methods=['GET'])
@app.route('/info/users/<platform>', methods=['GET'])
def info_users(platform=None):
    """
    Return a dictionary of users optionally filtering by platform

    :param platform:
    """
    users = user_summary(platform)
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

    for platform, count in platform_summary():
        d[platform] = {'releases': count}
    return jsonify(d), 200


