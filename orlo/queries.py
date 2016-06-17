from __future__ import print_function
import datetime
import arrow
from orlo import app
from orlo.orm import db, Release, Platform, Package, release_platform
from orlo.exceptions import OrloError, InvalidUsage
from sqlalchemy import and_, exc

__author__ = 'alforbes'

"""
Functions in this file are about generating summaries of data
"""


def get_release(release_id):
    """
    Fetch a single release

    :param release_id:
    :return:
    """
    return db.session.query(Release).filter(Release.id == release_id)


def filter_release_status(query, status):
    """
    Filter the given query by the given release status

    Release status is special, because it's actually determined by the
    package status

    :param query: Query object
    :param status: The status to filter on
    :return:
    """
    enums = Package.status.property.columns[0].type.enums
    if status not in enums:
        raise InvalidUsage("Invalid package status, {} is not in {}".format(
            status, str(enums)))
    if status in ["SUCCESSFUL", "NOT_STARTED"]:
        # ALL packages must match this status for it to apply to the release
        # Query logic translates to "Releases which do not have any packages
        # which satisfy
        # the condition 'Package.status != status'". I.E, all match.
        query = query.filter(
            ~Release.packages.any(
                Package.status != status
            ))
    elif status in ["FAILED", "IN_PROGRESS"]:
        # ANY package can match for this status to apply to the release
        query = query.filter(Release.packages.any(Package.status == status))
    return query


def filter_release_rollback(query, rollback):
    """
    Filter the given query by whether the releases are rollbacks or not

    :param query: Query object
    :param boolean rollback:
    :return:
    """
    if rollback is True:
        # Only count releases which have a rollback package
        query = query.filter(
            Release.packages.any(Package.rollback == True)
        )
    elif rollback is False:
        # Only count releases which do not have any rollback packages
        query = query.filter(
            ~Release.packages.any(Package.rollback == True)
        )
    else:  # What the hell did you pass?
        raise TypeError(
            "Bad rollback parameter: '{}', type {}. Boolean expected.".format(
                rollback, type(rollback)))
    return query


def apply_filters(query, args):
    """
    Apply filters to a query

    :param query: Query object to apply filters to
    :param args: Dictionary of arguments, usually request.args

    :return: filtered query object
    """

    for field, value in args.items():
        if field == 'latest':  # this is not a comparison
            continue

        # special logic for these ones, as they are release attributes that
        # are JIT calculated from package attributes
        if field == 'status':
            query = filter_release_status(query, value)
            continue
        if field == 'rollback':
            query = filter_release_rollback(query, value)
            continue

        if field.startswith('package_'):
            # Package attribute. Ensure source query does a join on Package.
            db_table = Package
            field = '_'.join(field.split('_')[1:])
        else:
            db_table = Release

        comparison = '=='
        time_absolute = False
        time_delta = False
        strip_last = False
        sub_field = None

        if field.endswith('_gt'):
            strip_last = True
            comparison = '>'
        if field.endswith('_lt'):
            strip_last = True
            comparison = '<'
        if field.endswith('_before'):
            strip_last = True
            comparison = '<'
            time_absolute = True
        if field.endswith('_after'):
            strip_last = True
            comparison = '>'
            time_absolute = True
        if 'duration' in field.split('_'):
            time_delta = True
        if field == 'platform':
            field = 'platforms'
            comparison = 'any'
            sub_field = Platform.name

        if strip_last:
            # Strip anything after the last underscore inclusive
            field = '_'.join(field.split('_')[:-1])

        filter_field = getattr(db_table, field)

        # Booleans
        if value in ('True', 'true'):
            value = True
        if value in ('False', 'false'):
            value = False

        # Time related
        if time_delta:
            value = datetime.timedelta(seconds=int(value))
        if time_absolute:
            value = arrow.get(value)

        # Do comparisons
        app.logger.debug(
            "Filtering: {} {} {}".format(filter_field, comparison, value))
        if comparison == '==':
            query = query.filter(filter_field == value)
        if comparison == '<':
            query = query.filter(filter_field < value)
        if comparison == '>':
            query = query.filter(filter_field > value)
        if comparison == 'any':
            query = query.filter(filter_field.any(sub_field == value))

    return query


def releases(**kwargs):
    """
    Return whole releases, based on filters

    :param kwargs: Request arguments
    :return:
    """

    limit = kwargs.pop('limit', None)
    offset = kwargs.pop('offset', None)
    desc = kwargs.pop('desc', False)

    if any(field.startswith('package_') for field in kwargs.keys()) \
            or "status" in kwargs.keys():
        # Package attributes need the join, as does status as it's really a
        # package attribute
        query = db.session.query(Release).join(Package)
    else:
        # No need to join on package if none of our params need it
        query = db.session.query(Release)

    for key in kwargs.keys():
        if isinstance(kwargs[key], bool):
            continue
        if kwargs[key].lower() in ['null', 'none']:
            kwargs[key] = None
    try:
        query = apply_filters(query, kwargs)
    except AttributeError as e:
        raise InvalidUsage(
            "An invalid field was specified: {}".format(e.args[0]))

    if desc:
        stime_field = Release.stime.desc
    else:
        stime_field = Release.stime.asc

    query = query.order_by(stime_field())

    if limit:
        try:
            limit = int(limit)
        except ValueError:
            raise InvalidUsage("limit must be a valid integer value")
        query = query.limit(limit)
    if offset:
        try:
            offset = int(offset)
        except ValueError:
            raise InvalidUsage("offset must be a valid integer value")
        query = query.offset(offset)

    return query


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


def user_info(username):
    """
    Get user info for a single user

    :param username:
    :return:
    """
    query = db.session.query(
        Release.user, db.func.count(Release.id)) \
        .filter(Release.user == username) \
        .group_by(Release.user)

    return query


def user_list(platform=None):
    """
    Find all users that have performed releases

    :param platform: Platform to filter on
    """
    query = db.session.query(Release.user.distinct())
    if platform:
        query = query.filter(Release.platforms.any(Platform.name == platform))

    return query


def team_summary(platform=None):
    """
    Find all teams that have performed releases and how many

    :param platform: Platform to filter on
    :return: Query result [('team', release_count)]
    """

    query = db.session.query(Release.team, db.func.count(Release.id))
    if platform:
        query = query.filter(Release.platforms.any(Platform.name == platform))

    return query.group_by(Release.team)


def team_info(team_name):
    """
    Get info for a single team

    :param team_name:
    :return:
    """
    query = db.session.query(
        Release.user, db.func.count(Release.id)) \
        .filter(Release.team == team_name) \
        .group_by(Release.team)

    return query


def team_list(platform=None):
    """
    Find all teams that have performed releases

    :param platform: Platform to filter on
    """
    query = db.session.query(Release.team.distinct())
    if platform:
        query = query.filter(Release.platforms.any(Platform.name == platform))

    return query


def package_summary(platform=None, stime=None, ftime=None):
    """
    Summary of packages

    :param stime: Start time, or time lower bound
    :param ftime: Finish time, or time upper bound
    :param platform: Filter by platform
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


def package_info(package_name):
    """
    Return a query for a package and how many times it was released

    :param package_name:
    :return:
    """
    query = db.session.query(
        Package.name, db.func.count(Package.id)) \
        .filter(Package.name == package_name) \
        .group_by(Package.name)

    return query


def package_list(platform=None):
    """
    Find all packages that have been released

    :param platform: Platform to filter on
    """
    query = db.session.query(Package.name).distinct()
    if platform:
        query = query.join(Release).filter(
            Release.platforms.any(Platform.name == platform))

    return query


def package_versions(platform=None):
    """
    List the current version of all packages

    It is not sufficient to just return the highest version of each successful
    package, as they can be rolled back, so we determine the version by last
    release time

    :param platform: Platform to filter on
    """

    # Sub query gets a list of successful packages by last successful release
    # time
    sub_q = db.session.query(
            Package.name.label('name'),
            db.func.max(Package.stime).label('max_stime')) \
        .filter(Package.status == 'SUCCESSFUL')
    if platform:  # filter by platform
        sub_q = sub_q \
            .join(Release) \
            .filter(Release.platforms.any(Platform.name == platform))
    sub_q = sub_q \
        .group_by(Package.name) \
        .subquery()

    # q inner-joins Package table with sub_q to get the version
    q = db.session.query(
            Package.name,
            Package.version) \
        .join(sub_q, and_(sub_q.c.max_stime == Package.stime,
                          sub_q.c.name == Package.name)) \
        .group_by(Package.name, Package.version)

    return q


def count_releases(user=None, package=None, team=None, platform=None,
                   status=None, rollback=None, stime=None, ftime=None):
    """
    Return the number of releases with the attributes specified

    :param string user: Filter by username
    :param string package:  Filter by package
    :param string team:  Filter by team
    :param string status:  Filter by status
    :param string platform: Filter by platform
    :param string stime: Filter by releases that started after
    :param string ftime: Filter by releases that started before
    :param boolean rollback: Filter on whether or not the release contains a \
    rollback
    :return: Query

    Note that rollback and status are special fields when applied to a
    release, as they are Package attributes.

    A "successful" or "in progress" release is defined as a release where all
    packages match the status. Conversely, a "failed" or "not started" release
    is defined as a release where any package matches.

    For rollbacks, if any package is a rollback the release is included,
    otherwise if all packages are not rollbacks the release obviously isn't
    either.

    Implication of this is that a release can be both "failed" and "in
    progress".
    """

    args = {
        'user': user, 'package': package, 'team': team, 'platform': platform,
        'status': status, 'rollback': rollback, 'stime': stime, 'ftime': ftime,
    }
    app.logger.debug("Entered count_releases with args: {}".format(str(args)))

    query = db.session.query(db.func.count(Release.id.distinct())).join(Package)

    if platform:
        query = query.filter(Release.platforms.any(Platform.name == platform))
    if user:
        query = query.filter(Release.user == user)
    if team:
        query = query.filter(Release.team == team)
    if package:
        query = query.filter(Package.name == package)
    if stime:
        query = query.filter(Release.stime >= stime)
    if ftime:
        query = query.filter(Release.stime <= ftime)

    if rollback is not None:
        query = filter_release_rollback(query, rollback)

    if status:
        query = filter_release_status(query, status)

    return query


def count_packages(user=None, team=None, platform=None, status=None,
                   rollback=None):
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


def platform_info(platform_name):
    """
    Return a single platform and how many times it was released

    :param platform_name:
    :return:
    """

    query = db.session.query(
        Platform.name, db.func.count(Platform.id)) \
        .filter(Platform.name == platform_name) \
        .group_by(Platform.name)

    return query


def platform_list():
    """
    Return a summary of the known platforms

    :return: Query result [('platform'), release_count]
    """

    query = db.session.query(Platform.name.distinct()) \
        .join(release_platform)

    return query
