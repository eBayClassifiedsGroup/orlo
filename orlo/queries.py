from __future__ import print_function
from orlo.orm import db, Release, Platform, Package, release_platform

__author__ = 'alforbes'

"""
Functions in this file are about generating summaries of data
"""


def user_summary(platform=None):
    """
    Find all users that have performed releases and how many

    :param platform: Platform to filter on
    :return: Query result [('user', release_count)]
    """

    query = db.session.query(Release.user, db.func.count(Release.id))
    if platform:
        query = query.filter(Release.platforms.any(Platform.name == platform))

    return query.group_by(Release.user)


def user_list(platform=None):
    """
    Find all users that have performed releases

    :param platform: Platform to filter on
    """
    query = db.session.query(Release.user)
    if platform:
        query = query.filter(Release.platforms.any(Platform.name == platform))

    return query


def package_summary(platform=None, stime=None, ftime=None):
    """
    Summary of releases by package

    :param stime: Start time, or time lower bound
    :param ftime: Finish time, or time upper bound
    :param platform:
    """

    query = db.session.query(Package.name, db.func.count(Package.release_id))
    if any(x is not None for x in [platform, stime, ftime]):
        query = query.join(Release)
    if platform:
        query = query.filter(Release.platforms.any(Platform.name == platform))
    if stime:
        query = query.filter(Release.stime > stime)
    if ftime:
        query = query.filter(Release.stime < ftime)

    query = query.group_by(Package.name)

    return query


def package_list(platform=None):
    """
    Find all packages that have been released

    :param platform: Platform to filter on
    """
    query = db.session.query(Package.name).distinct()
    if platform:
        query = query.join(Release).filter(Release.platforms.any(Platform.name == platform))

    return query


def package_versions(platform=None):
    """
    List the current version of all packages

    It is not sufficient to just return the highest version of each successful package,
    as they can be rolled back, so we get the max stime

    :param platform: Platform to filter on
    """

    q = db.session.query(
            Package.name,
            Package.version,
            db.func.max(Package.stime).label('last_release'),
        )
    if platform:
        q = q.join(Release).filter(Release.platforms.any(Platform.name == platform))

    q = q\
        .filter(Package.status == 'SUCCESSFUL')\
        .group_by(Package.name)

    return q


def releases_successful(platform=None):
    """
    Return the number of successful releases

    Note that a "successful" release is defined as a release where all packages are recorded as
    successful, therefore the query below filters out any releases which contain a package which
    is not successful.

    :param platform: Platform to filter on
    :return: Int
    """

    query = db.session.query(Release.id, db.func.count(Package.id)).join(Package)

    if platform:
        query = query.filter(Release.platforms.any(Platform.name == platform))

    query = query.filter(~Release.packages.any(
            db.or_(Package.status != "SUCCESSFUL"))) \
        .group_by(Release.id)

    return query


def platform_summary():
    """
    Return a summary of the known platforms

    :return: Query result [('platform'), release_count]
    """

    query = db.session.query(
            Platform.name, db.func.count(Platform.id)) \
        .join(release_platform) \
        .group_by(Platform.name)

    return query
