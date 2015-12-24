from __future__ import print_function
from orlo.orm import db, Release, Platform, Package, release_platform
from orlo.exceptions import OrloError

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
            Package.version, db.func.max(Package.stime).label('last_release'),
        )
    if platform:
        q = q.join(Release).filter(Release.platforms.any(Platform.name == platform))

    q = q\
        .filter(Package.status == 'SUCCESSFUL')\
        .group_by(Package.name)

    return q


def count_releases(user=None, package=None, team=None, platform=None, status=None, rollback=None):
    """
    Return the number of releases with the attributes specified

    :param string user: Filter by username
    :param string package:  Filter by package
    :param string team:  Filter by team
    :param string status:  Filter by status
    :param string platform: Platform to filter on
    :param boolean rollback: Filter on whether or not the release contains a rollback
    :return: Query

    Note that rollback and status are special fields as they are Package attributes.
    A "successful" or "in progress" release is defined as a release where all packages match the
    status. Conversely, a "failed" or "not started" release is defined as a release where any
    package matches.

    For rollbacks, if any package is a rollback, the release is included, otherwise it is not.

    Implication of this is that a release can be both "failed" and "in progress".
    """

    query = db.session.query(db.func.count(Release.id.distinct())).join(Package)

    if platform:
        query = query.filter(Release.platforms.any(Platform.name == platform))
    if user:
        query = query.filter(Release.user == user)
    if team:
        query = query.filter(Release.team == team)
    if package:
        query = query.filter(Package.name == package)

    if rollback is not None:
        if rollback is True:
            # Only count release which have a rollback package
            query = query.filter(
                Release.packages.any(Package.rollback == True)
            )
        elif rollback is False:
            # Only count releases which do not have any rollback packages
            query = query.filter(
                ~Release.packages.any(Package.rollback == True)
            )
        else:  # What the hell did you pass?
            raise TypeError("Bad rollback parameter: '{}', type {}. Boolean expected.".format(
                    rollback, type(rollback)))

    if status:
        enums = Package.status.property.columns[0].type.enums
        if status not in enums:
            raise OrloError("Invalid package status, {} is not in {}".format(
                status, str(enums)))
        if status in ["SUCCESSFUL", "NOT_STARTED"]:
            # ALL packages must match this status for it to apply to the release
            # Query logic translates to "Releases which do not have any packages which satisfy
            # the condition 'Package.status != status'". I.E, all match.
            query = query.filter(
                    ~Release.packages.any(
                        Package.status != status
                    ))
        elif status in ["FAILED", "IN_PROGRESS"]:
            # ANY package can match for this status to apply to the release
            query = query.filter(Release.packages.any(Package.status == status))

    return query


def count_packages(user=None, team=None, platform=None, status=None, rollback=None):
    """
    Return the number of packages with the attributes specified

    :param string user:
    :param string team:
    :param string platform:
    :param string status:
    :param boolean rollback:
    :return: Query
    """

    query = db.session.query(db.func.count(Package.id.distinct())).join(Release)

    if platform:
        query = query.filter(Release.platforms.any(Platform.name == platform))
    if user:
        query = query.filter(Release.user == user)
    if team:
        query = query.filter(Release.team == team)
    if status:
        query = query.filter(Package.status == status)
    if rollback is not None:
        query = query.filter(Package.rollback == rollback)

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
