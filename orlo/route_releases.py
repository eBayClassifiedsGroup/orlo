from flask import jsonify, request, Response, json, g
from orlo import app, queries, config
from orlo.exceptions import InvalidUsage
from orlo.user_auth import token_auth
from orlo.orm import db, Release, Package, PackageResult, ReleaseNote, \
    ReleaseMetadata, Platform
from orlo.util import validate_request_json, create_release, \
    validate_release_input, validate_package_input, fetch_release, \
    create_package, fetch_package, stream_json_list, str_to_bool, is_uuid
from orlo.deploy import ShellDeploy
from orlo.user_auth import conditional_auth

security_enabled = config.getboolean('security', 'enabled')


@app.route('/releases', methods=['POST'])
@conditional_auth(conditional_auth(token_auth.token_required))
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
        -d '{"note": "blah", "platforms": ["site1"], "references": ["ticket"],
        "team": "A-Team", "user": "aforbes"}'
    """
    validate_release_input(request)
    release = create_release(request)

    if request.json.get('note'):
        release_note = ReleaseNote(release.id, request.json.get('note'))
        db.session.add(release_note)

    if request.json.get('metadata'):
        for key, value in request.json.get('metadata').items():
            metadata = ReleaseMetadata(release.id, key, value)
            db.session.add(metadata)

    app.logger.info(
        'Create release {}, references: {}, platforms: {}'.format(
            release.id, release.notes, release.references, release.platforms,
            release.metadata)
    )

    release.start()

    db.session.add(release)
    db.session.commit()

    return jsonify(id=release.id)


@app.route('/releases/<release_id>/packages', methods=['POST'])
@conditional_auth(token_auth.token_required)
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
        -X POST http://127.0.0.1/releases/${RELEASE_ID}/packages \\
        -d '{"name": "test-package", "version": "1.0.1"}'
    """
    validate_package_input(request, release_id)

    release = fetch_release(release_id)
    package = create_package(release.id, request)

    app.logger.info(
        'Create package {}, release {}, name {}, version {}'.format(
            package.id, release.id, request.json['name'],
            request.json['version']))

    db.session.add(package)
    db.session.commit()

    return jsonify(id=package.id)


@app.route('/releases/<release_id>/packages/<package_id>/results',
           methods=['POST'])
@conditional_auth(token_auth.token_required)
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


@app.route('/releases/<release_id>/deploy', methods=['POST'])
@conditional_auth(token_auth.token_required)
def post_releases_deploy(release_id):
    """
    Deploy a Release

    :param string release_id: Release UUID

    **Example curl**:

    .. sourcecode:: shell

        curl -H "Content-Type: application/json" \\
        -X POST http://127.0.0.1/releases/${RELEASE_ID}/deploy
    """
    release = fetch_release(release_id)
    app.logger.info("Release start, release {}".format(release_id))

    release.start()
    db.session.add(release)
    db.session.commit()

    # TODO call deploy Class start Method, i.e. pure python rather than shell
    deploy = ShellDeploy(release)
    output = deploy.start()
    return jsonify(output), 200


@app.route('/releases/<release_id>/start', methods=['POST'])
@conditional_auth(token_auth.token_required)
def post_releases_start(release_id):
    """
    Indicate that a release is starting

    :param release_id:
    :return:
    """
    release = fetch_release(release_id)
    app.logger.info("Release start, release {}".format(release_id))
    release.start()

    db.session.add(release)
    db.session.commit()
    return '', 204


@app.route('/releases/<release_id>/stop', methods=['POST'])
@conditional_auth(token_auth.token_required)
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
    release = fetch_release(release_id)
    # TODO check that all packages have been finished
    app.logger.info("Release stop, release {}".format(release_id))
    release.stop()

    db.session.add(release)
    db.session.commit()
    return '', 204


@app.route('/releases/<release_id>/packages/<package_id>/start',
           methods=['POST'])
@conditional_auth(token_auth.token_required)
def post_packages_start(release_id, package_id):
    """
    Indicate that a package has started deploying

    :param string release_id: Release UUID
    :param string package_id: Package UUID
    :status 204:

    **Example curl**:

    .. sourcecode:: shell

        curl -X POST http://127.0.0.1/releases/${RELEASE_ID}/packages/${
        PACKAGE_ID}/start
    """
    package = fetch_package(release_id, package_id)
    app.logger.info("Package start, release {}, package {}".format(
        release_id, package_id))
    package.start()

    db.session.add(package)
    db.session.commit()
    return '', 204


@app.route('/releases/<release_id>/packages/<package_id>/stop',
           methods=['POST'])
@conditional_auth(token_auth.token_required)
def post_packages_stop(release_id, package_id):
    """
    Indicate that a package has finished deploying

    **Example curl**:

    .. sourcecode:: shell

        curl -H "Content-Type: application/json" \\
        -X POST \\
        http://127.0.0.1/releases/${RELEASE_ID}/packages/${PACKAGE_ID}/stop \\
        -d '{"success": "true"}'

    :param string package_id: Package UUID
    :param string release_id: Release UUID
    """
    validate_request_json(request)
    success = request.json.get('success') in [True, 'True', 'true', '1']

    package = fetch_package(release_id, package_id)
    app.logger.info("Package stop, release {}, package {}, success {}".format(
        release_id, package_id, success))
    package.stop(success=success)

    db.session.add(package)
    db.session.commit()
    return '', 204


@app.route('/releases/<release_id>/notes', methods=['POST'])
@conditional_auth(token_auth.token_required)
def post_releases_notes(release_id):
    """
    Add a note to a release

    :param string release_id: Release UUID
    :query string text: Text
    :return:
    """
    validate_request_json(request)
    text = request.json.get('text')
    if not text:
        raise InvalidUsage("Must include text in posted document")

    note = ReleaseNote(release_id, text)
    app.logger.info("Adding note to release {}".format(release_id))
    db.session.add(note)
    db.session.commit()
    return '', 204


@app.route('/releases/<release_id>/metadata', methods=['POST'])
@conditional_auth(token_auth.token_required)
def post_releases_metadata(release_id):
    """
    Add metadata to a release

    :param string release_id: Release UUID
    :query string text: Text
    :return:
    """
    validate_request_json(request)
    meta = request
    if not meta:
        raise InvalidUsage(
            "Must include metadata in posted document: es {\"key\" : "
            "\"value\"}")

    for key, value in request.json.items():
        app.logger.info("Adding Metadata to release {}".format(release_id))
        metadata = ReleaseMetadata(release_id, key, value)
        db.session.add(metadata)

    db.session.commit()
    return '', 204


@app.route('/releases', methods=['GET'])
@app.route('/releases/<release_id>', methods=['GET'])
def get_releases(release_id=None):
    """
    Return a list of releases to the client, filters optional

    :param string release_id: Optionally specify a single release UUID to
    fetch. \
        This does not disable filters.
    :query int desc: Normally results are returned ordered by stime
    ascending, setting
        desc to true will reverse this and sort by stime descending
    :query int limit: Limit the results by int
    :query int offset: Offset the results by int
    :query string package_name: Filter releases by package name
    :query string user: Filter releases by user the that performed the release
    :query string platform: Filter releases by platform
    :query string stime_before: Only include releases that started before \
    timestamp given
    :query string stime_after: Only include releases that started after \
    timestamp given
    :query string ftime_before: Only include releases that finished before \
    timestamp given
    :query string ftime_after: Only include releases that finished after \
    timestamp given
    :query string team: Filter releases by team
    :query string status: Filter by release status. This field is calculated \
    from the package status, see special note below.
    :query int duration_lt: Only include releases that took less than (int) \
    seconds
    :query int duration_gt: Only include releases that took more than (int) \
    seconds
    :query boolean package_rollback: Filter on whether or not the releases \
    contain a rollback
    :query string package_name: Filter by package name
    :query string package_version: Filter by package version
    :query int package_duration_gt: Filter by packages of duration greater than
    :query int package_duration_lt: Filter by packages of duration less than
    :query string package_status: Filter by package status. Valid statuses are:\
         "NOT_STARTED", "IN_PROGRESS", "SUCCESSFUL", "FAILED"

    **Note for time arguments**:
        The timestamp format you must use is specified in /etc/orlo/orlo.ini.
        All times are UTC.

    **Note on status**:
        The release status is calculated from the packages it contains. The
        possible values are the same as a package. For a release to be
        considered "SUCCESSFUL" or "NOT_STARTED", all packages must have this
        value. If any one package has the value "IN_PROGRESS" or "FAILED",
        that status applies to the whole release, with "FAILED" overriding
        "IN_PROGRESS".

    """

    booleans = ('rollback', 'package_rollback',)

    if release_id:  # Simple, just fetch one release
        if not is_uuid(release_id):
            raise InvalidUsage("Release ID given is not a valid UUID")
        query = queries.get_release(release_id)
    elif len([x for x in request.args.keys()]) == 0:
        raise InvalidUsage("Please specify a filter. See "
                           "http://orlo.readthedocs.org/en/latest/rest.html"
                           "#get--releases for more info")
    else:  # Bit more complex
        # Flatten args, as the ImmutableDict puts some values in a list when
        # expanded
        args = {}
        for k in request.args.keys():
            if k in booleans:
                args[k] = str_to_bool(request.args.get(k))
            else:
                args[k] = request.args.get(k)
        query = queries.releases(**args)

    # Execute eagerly to avoid confusing stack traces within the Response on
    # error
    db.session.execute(query)

    return Response(stream_json_list('releases', query),
                    content_type='application/json')
