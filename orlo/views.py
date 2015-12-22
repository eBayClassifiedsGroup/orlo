from orlo import app
from orlo.exceptions import InvalidUsage
from flask import jsonify, request, abort
import arrow
import datetime
from orm import db, Release, Package, PackageResult, ReleaseNote, Platform
from orlo.util import list_to_string
from sqlalchemy.orm import exc


@app.errorhandler(404)
def page_not_found(error):
    d = error.to_dict()
    d['url'] = request.url
    return jsonify(d), 404


@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.errorhandler(400)
def handle_400(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


def _create_release(request):
    """
    Create a Release object from a request
    """

    references = request.json.get('references', [])
    if references and type(references) is list:
        references = list_to_string(references)

    # If given a single string, make it a list
    request_platforms = request.json.get('platforms')
    if request_platforms and type(request_platforms) is not list:
        request_platforms = [request_platforms]

    # Get the platforms
    platforms = []
    for p in request_platforms:
        try:
            query = db.session.query(Platform).filter(Platform.name == p)
            platform = query.one()
            app.logger.debug("Found platform {}".format(platform))
        except exc.NoResultFound:
            app.logger.info("Creating platform {}".format(p))
            platform = Platform(p)
            db.session.add(platform)
        platforms.append(platform)

    release = Release(
        # Required attributes
        platforms=platforms,
        user=request.json['user'],
        # Not required
        team=request.json.get('team'),
        references=references,
    )
    return release


def _create_package(release_id, request):
    """
    Create a package object for a release
    """

    return Package(
        release_id,
        request.json.get('name'),
        request.json.get('version'),
        diff_url=request.json.get('diff_url', None),
        rollback=request.json.get('rollback', False),
    )


def _fetch_release(release_id):
    """
    Fetch a release by ID
    """
    rq = db.session.query(Release).filter(Release.id == release_id)
    release = rq.first()
    if not release:
        raise InvalidUsage("Release does not exist")
    return release


def _fetch_package(release_id, package_id):
    """
    Fetch a package, and validate it is part of the release
    """

    # Fetch release first, as it is a good sanity check
    _fetch_release(release_id)
    pq = db.session.query(Package).filter(Package.id == package_id)
    package = pq.first()

    if not package:
        raise InvalidUsage("Package does not exist")
    if str(package.release_id) != release_id:
        raise InvalidUsage("This package does not belong to this release")

    return package


def _validate_request_json(request):
    try:
        request.json
    except Exception:
        # This is pretty ugly, but we want something more user friendly than "Bad Request"
        raise InvalidUsage("Could not parse JSON document")

    if not request.json:
        raise InvalidUsage('Missing application/json header', status_code=400)


def _validate_release_input(request):
    _validate_request_json(request)
    if 'platforms' not in request.json:
        raise InvalidUsage('JSON doc missing platforms field', status_code=400)
    return True


def _validate_package_input(request, release_id):
    _validate_request_json(request)

    if not 'name' in request.json or not 'version' in request.json:
        raise InvalidUsage("Missing name / version in request body.")
    app.logger.debug("Package request validated, release_id {}".format(release_id))
    return True


def _validate_package_stop_input(request):
    _validate_request_json(request)
    if 'success' not in request.json:
        raise InvalidUsage("Missing success key in JSON doc")


@app.route('/ping', methods=['GET'])
def ping():
    """
    Simple ping test, takes no parameters

    **Example curl**:

    .. sourcecode:: shell

        curl -X GET 'http://127.0.0.1/ping'
    """
    return 'pong'


@app.route('/releases', methods=['POST'])
def post_releases():
    """
    Create a release - the first step in a deployment

    :<json string user: User that is performing the release
    :<json string team: The development team responsible for this release
    :<json array platforms: List of platforms receiving the release
    :<json array references: List of external references, e.g. Jira ticket
    :>json string id: UUID reference to the created release
    :reqheader Content-Type: Must be application/json
    :status 200: Release was created successfully
    :status 400: Invalid request

    **Example curl**:

    .. sourcecode:: shell

        curl -H "Content-Type: application/json" \\
        -X POST \\
        http://127.0.0.1/releases \\
        -d '{"note": "blah", "platforms": ["site1"], "references": ["ticket"], "team": "A-Team",
        "user": "aforbes"}'
    """
    _validate_release_input(request)
    release = _create_release(request)

    if request.json.get('note'):
        release_note = ReleaseNote(release.id, request.json.get('note'))
        db.session.add(release_note)

    app.logger.info(
        'Create release {}, references: {}, platforms: {}'.format(
            release.id, release.notes, release.references, release.platforms)
    )

    release.start()

    db.session.add(release)
    db.session.commit()

    return jsonify(id=release.id)


@app.route('/releases/<release_id>/packages', methods=['POST'])
def post_packages(release_id):
    """
    Add a package to a release

    :param string release_id: UUID of the release to add the package to
    :<json string name: Name of the package
    :<json string version: Version of the package
    :<json boolean rollback: Whether this package deploy is a rollback
    :>json string id: UUID reference to the created package
    :reqheader Content-Type: Must be application/json
    :status 200: Package was added to the release successfully
    :status 400: Invalid request
    **Example curl**:

    .. sourcecode:: shell

        curl -H "Content-Type: application/json" \\
        -X POST \\
        http://127.0.0.1/releases/${RELEASE_ID}/packages \\
        -d '{"name": "test-package", "version": "1.0.1"}'
    """
    _validate_package_input(request, release_id)

    release = _fetch_release(release_id)
    package = _create_package(release.id, request)

    app.logger.info(
        'Create package {}, release {}, name {}, version {}'.format(
            package.id, release.id, request.json['name'],
            request.json['version']))

    db.session.add(package)
    db.session.commit()

    return jsonify(id=package.id)


@app.route('/releases/<release_id>/packages/<package_id>/results',
           methods=['POST'])
def post_results(release_id, package_id):
    """
    Post the results of a package release

    :param string release_id: Release UUID
    :param string package_id: Package UUID
    :<json string content: Free text field to store what you wish
    :status 204: Package results added successfully
    """
    results = PackageResult(package_id, str(request.json))
    app.logger.info("Post results, release {}, package {}".format(
        release_id, package_id))
    db.session.add(results)
    db.session.commit()
    return '', 204


@app.route('/releases/<release_id>/stop', methods=['POST'])
def post_releases_stop(release_id):
    """
    Indicate that a release has finished

    This should be called after all packages have also been "stopped".
    In future it may stop any un-stopped packages.

    :param string release_id: Release UUID

    **Example curl**:

    .. sourcecode:: shell

        curl -H "Content-Type: application/json" \\
        -X POST http://127.0.0.1/releases/${RELEASE_ID}/stop
    """
    release = _fetch_release(release_id)
    # TODO check that all packages have been finished
    app.logger.info("Release stop, release {}".format(release_id))
    release.stop()

    db.session.add(release)
    db.session.commit()
    return '', 204


@app.route('/releases/<release_id>/packages/<package_id>/start',
           methods=['POST'])
def post_packages_start(release_id, package_id):
    """
    Indicate that a package has started deploying

    :param string release_id: Release UUID
    :param string package_id: Package UUID
    :status 204:

    **Example curl**:

    .. sourcecode:: shell

        curl -X POST http://127.0.0.1/releases/${RELEASE_ID}/packages/${PACKAGE_ID}/start
    """
    package = _fetch_package(release_id, package_id)
    app.logger.info("Package start, release {}, package {}".format(
        release_id, package_id))
    package.start()

    db.session.add(package)
    db.session.commit()
    return '', 204


@app.route('/releases/<release_id>/packages/<package_id>/stop',
           methods=['POST'])
def post_packages_stop(release_id, package_id):
    """
    Indicate that a package has finished deploying

    **Example curl**:

    .. sourcecode:: shell

        curl -H "Content-Type: application/json" \\
        -X POST http://127.0.0.1/releases/${RELEASE_ID}/packages/${PACKAGE_ID}/stop \\
        -d '{"success": "true"}'

    :param string package_id: Package UUID
    :param string release_id: Release UUID
    """
    _validate_request_json(request)
    success = request.json.get('success') in ['True', 'true', '1']

    package = _fetch_package(release_id, package_id)
    app.logger.info("Package stop, release {}, package {}, success {}".format(
        release_id, package_id, success))
    package.stop(success=success)

    db.session.add(package)
    db.session.commit()
    return '', 204


@app.route('/releases/<release_id>/notes', methods=['POST'])
def post_releases_notes(release_id):
    """
    Add a note to a release

    :param string release_id: Release UUID
    :param string text: Text
    :return:
    """
    _validate_request_json(request)
    text = request.json.get('text')
    if not text:
        raise InvalidUsage("Must include text in posted document")

    note = ReleaseNote(release_id, text)
    app.logger.info("Adding note to release {}".format(release_id))
    db.session.add(note)
    db.session.commit()
    return '', 204


@app.route('/releases', methods=['GET'])
@app.route('/releases/<release_id>', methods=['GET'])
def get_releases(release_id=None):
    """
    Return a list of releases to the client, filters optional

    :param string release_id: Optionally specify a single release UUID to fetch. This does not
    disable filters.
    :query boolean last: Return only the last matching release (the latest)
    :query string package_name: Filter releases by package name
    :query string user: Filter releases by user the that performed the release
    :query string platform: Filter releases by platform
    :query string stime_before: Only include releases that started before timestamp given
    :query string stime_after: Only include releases that started after timestamp given
    :query string ftime_before: Only include releases that finished before timestamp given
    :query string ftime_after: Only include releases that finished after timestamp given
    :query string team: Filter releases by team

    **Note for time arguments**:
        The timestamp format you must use is specified in /etc/orlo.conf. All times are UTC.

    .. versionadded:: 0.0.4
    :query int duration_lt: Only include releases that took less than (int) seconds
    :query int duration_gt: Only include releases that took more than (int) seconds
    :query boolean package_rollback: Filter on whether or not the releases contain a rollback
    :query string package_name: Filter by package name
    :query string package_version: Filter by package version
    :query int package_duration_gt: Filter by packages of duration greater than
    :query int package_duration_lt: Filter by packages of duration less than
    :query string package_status: Filter by package status. Valid statuses are "NOT_STARTED",
    "IN_PROGRESS", "SUCCESSFUL", "FAILED"
    """

    if any(field.startswith('package_') for field in request.args.keys()):
        query = db.session.query(Release).join(Package)
    else:
        # No need to join on package if none of our params need it
        query = db.session.query(Release)

    if request.args.get('last', False):
        # sort descending so we can use .first()
        query = query.order_by(Release.stime.desc())
    else:  # ascending
        query = query.order_by(Release.stime.asc())

    if release_id:
        query = query.filter(Release.id == release_id)
    elif request.args:
        query = apply_filters(query, request.args)

    if request.args.get('latest'):
        releases = [query.first()]
    else:
        releases = query.all()

    app.logger.debug("Returning {} releases".format(len(releases)))
    output = []
    for r in releases:
        output.append(r.to_dict())

    return jsonify(releases=output), 200


def apply_filters(query, args):
    """
    Apply filters to a query

    :param query: Query object to apply filters to
    :param args: Dictionary of arguments, usually request.args

    :return: filtered query object
    """

    for field, value in args.iteritems():
        if field == 'latest':  # this is not a comparison
            continue

        if field.startswith('package_'):
            # Package attribute
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
        app.logger.debug("Filtering: {} {} {}".format(filter_field, comparison, value))
        if comparison == '==':
            query = query.filter(filter_field == value)
        if comparison == '<':
            query = query.filter(filter_field < value)
        if comparison == '>':
            query = query.filter(filter_field > value)
        if comparison == 'any':
            query = query.filter(filter_field.any(sub_field == value))

    return query



