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
@app.route('/info/users/<platform>', methods=['GET'])
def info_users(platform=None):
    """
    Return a dictionary of users optionally filtering by platform

    :param platform:
    """
    users = queries.user_summary(platform)
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

    for platform, count in queries.platform_summary():
        d[platform] = {'releases': count}
    return jsonify(d), 200


@app.route('/info/packages', methods=['GET'])
@app.route('/info/packages/<platform>', methods=['GET'])
def info_packages(platform=None):
    """
    Summary of packages
    :param platform:
    """
    q = queries.package_summary(platform=platform)

    packages = {}

    for package, count in q.all():
        packages[package] = {'releases': count}
    return jsonify(packages), 200


@app.route('/info/package_list', methods=['GET'])
@app.route('/info/package_list/<platform>', methods=['GET'])
def info_package_list(platform=None):
    """
    Return list of all known packages
    :param platform:
    """
    q = queries.package_list(platform=platform)
    result = q.all()
    packages = [r[0] for r in result]
    return jsonify({'packages': packages}), 200


@app.route('/info/package_versions', methods=['GET'])
@app.route('/info/package_versions/<platform>', methods=['GET'])
def info_package_versions(platform=None):
    """
    Return current version of all packages
    :param platform:
    """
    q = queries.package_versions(platform=platform)
    result = q.all()

    packages = {}
    for package in result:
        packages[package[0]] = package[1]

    return jsonify(packages), 200
