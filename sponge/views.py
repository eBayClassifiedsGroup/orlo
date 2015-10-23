from sponge import app
from sponge.exceptions import InvalidUsage
from flask import jsonify, request, abort
import uuid
from collections import OrderedDict
from datetime import datetime
from orm import db, DbRelease, DbPackage, DbResults


@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


def _create_release(request):
    """
    Create a DbRelease object from a request
    """

    return DbRelease(
        # Required attributes
        platforms=request.json['platforms'],
        user=request.json['user'],
        # Not required
        notes=request.json.get('notes'),
        team=request.json.get('team'),
        references=request.json.get('references', []),
    )


def _create_package(release_id, request):
    """
    Create a package object for a release
    """

    return DbPackage(
        release_id,
        request.json['name'],
        request.json['version'],
    )


def _fetch_release(release_id):
    """
    Fetch a release by ID
    """
    rq = db.session.query(DbRelease).filter(DbRelease.id == release_id)
    dbRelease = rq.first()
    if not dbRelease:
        raise InvalidUsage("Release does not exist")
    return dbRelease


def _fetch_package(release_id, package_id):
    """
    Fetch a package, and validate it is part of the release
    """

    # Fetch release first, as it is a good sanity check
    _fetch_release(release_id)
    pq = db.session.query(DbPackage).filter(DbPackage.id == package_id)
    dbPackage = pq.first()

    if not dbPackage:
        raise InvalidUsage("Package does not exist")
    if str(dbPackage.release_id) != release_id:
        raise InvalidUsage("This package does not belong to this release")

    return dbPackage


def _validate_release_input(request):
    if not request.json:
        raise(InvalidUsage('Missing application/json header', status_code=400))
    if 'platforms' not in request.json:
        raise(InvalidUsage('JSON doc missing platforms field', status_code=400))
    return True


def _validate_package_input(request, id):
    if not request.json:
        raise InvalidUsage("Missing JSON body")
    if not 'name' in request.json or not 'version' in request.json:
        raise InvalidUsage("Missing name / version in request body.")
    return True


@app.route('/ping', methods=['GET'])
def ping():
    return 'pong'


@app.route('/releases', methods=['POST'])
def post_releases():
    """
    Posting a release - the first step in a deployment
    """
    _validate_release_input(request)
    release = _create_release(request)

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
    """
    _validate_package_input(request, id)

    dbRelease = _fetch_release(release_id)
    dbPackage = _create_package(dbRelease.id, request)

    app.logger.info(
        'Create package {}, release {}, name {}, version {}'.format(
            dbPackage.id, dbRelease.id, request.json['name'],
            request.json['version']))

    db.session.add(dbPackage)
    db.session.commit()

    return jsonify(id=dbPackage.id)


@app.route('/releases/<release_id>/packages/<package_id>/results',
           methods=['POST'])
def post_results(release_id, package_id):
    dbResults = DbResults(package_id, str(request.json))
    app.logger.info("Post results, release {}, package {}".format(
        release_id, package_id))
    db.session.add(dbResults)
    db.session.commit()
    return '', 204


@app.route('/releases/<release_id>/stop', methods=['POST'])
def post_releases_stop(release_id):
    """
    Indicate that a release has finished
    """
    dbRelease = _fetch_release(release_id)
    # TODO check that all packages have been finished
    app.logger.info("Release stop, release {}".format(release_id))

    dbRelease.stop()
    return '', 204


@app.route('/releases/<release_id>/packages/<package_id>/start',
           methods=['POST'])
def post_packages_start(release_id, package_id):
    """
    Indicate that a package has started deploying
    """
    dbPackage = _fetch_package(release_id, package_id)
    app.logger.info("Package start, release {}, package {}".format(
        release_id, package_id))
    dbPackage.start()

    db.session.add(dbPackage)
    db.session.commit()
    return '', 204


@app.route('/releases/<release_id>/packages/<package_id>/stop',
           methods=['POST'])
def post_packages_stop(release_id, package_id):
    """
    Indicate that a package has finished deploying
    """
    success = request.json['success']
    dbPackage = _fetch_package(release_id, package_id)
    app.logger.info("Package stop, release {}, package {}, success {}".format(
        release_id, package_id, success))
    dbPackage.stop(success=success)

    db.session.add(dbPackage)
    db.session.commit()
    return '', 204


@app.route('/releases', methods=['GET'])
def get_releases():
    """
    Return a list of releases to the client, filters optional
    """
    query = db.session.query(DbRelease).order_by(DbRelease.stime.asc())

    if 'package_name' in request.args:
        query = query.join(DbPackage).filter(DbPackage.name == request.args['package_name'])
    if 'user' in request.args:
        query = query.filter(DbRelease.user == request.args['user'])

    releases = query.all()
    output = []
    for r in releases:
        output.append(r.to_dict())

    return jsonify(releases=output), 200




