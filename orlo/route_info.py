from __future__ import print_function
from flask import request, jsonify, url_for
from orlo import app
import orlo.queries as queries

__author__ = 'alforbes'


def has_no_empty_params(rule):
    defaults = rule.defaults if rule.defaults is not None else ()
    arguments = rule.arguments if rule.arguments is not None else ()
    return len(defaults) >= len(arguments)


@app.route('/info', methods=['GET'])
def info_root():
    """
    Root of /info
    """
    urls = []
    for rule in app.url_map.iter_rules():
        base = str(rule).split('/')[1]
        if base == 'info':
            urls.append(str(rule))

    return jsonify({
        'message': '/info endpoint',
        'urls': sorted(urls),
    }), 200


@app.route('/info/users', methods=['GET'])
@app.route('/info/users/<username>', methods=['GET'])
def info_users(username=None):
    """
    Return a dictionary of users optionally filtering by platform

    :param username: Username to get info for
    :query platform: Platform to filter on
    """
    platform = request.args.get('platform')

    if username:
        users = queries.user_info(username)
    else:
        users = queries.user_summary(platform)

    d = {}
    for user, count in users:
        d[user] = {'releases': count}

    return jsonify(d), 200


@app.route('/info/platforms', methods=['GET'])
@app.route('/info/platforms/<platform>', methods=['GET'])
def info_platforms(platform=None):
    """
    Return a summary of the platforms

    :param platform: Platform to get info for
    """
    if platform:
        platforms = queries.platform_info(platform)
    else:
        platforms = queries.platform_summary()

    d = {}

    for platform, count in platforms:
        d[platform] = {'releases': count}
    return jsonify(d), 200


@app.route('/info/packages', methods=['GET'])
@app.route('/info/packages/<package>', methods=['GET'])
def info_packages(package=None):
    """
    Summary of packages

    :param package: Package to get info for
    :query platform: Platform to filter on
    """
    platform = request.args.get('platform')

    if package:
        packages = queries.package_info(package).all()
    else:
        packages = queries.package_summary(platform=platform).all()

    d = {}

    for package, count in packages:
        d[package] = {'releases': count}

    return jsonify(d), 200


@app.route('/info/packages/list', methods=['GET'])
def info_package_list():
    """
    Return list of all known packages

    :query platform: Platform to filter on
    """

    platform = request.args.get('platform')
    q = queries.package_list(platform=platform)
    result = q.all()
    packages = [r[0] for r in result]
    return jsonify({'packages': packages}), 200


@app.route('/info/packages/versions', methods=['GET'])
def info_package_versions():
    """
    Return current version of all packages

    :query platform:
    """
    platform = request.args.get('platform')
    q = queries.package_versions(platform=platform)
    result = q.all()

    packages = {}
    for package in result:
        packages[package[0]] = package[1]

    return jsonify(packages), 200
