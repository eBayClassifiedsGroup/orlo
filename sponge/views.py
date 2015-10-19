from sponge import app
from sponge.exceptions import InvalidUsage
from flask import jsonify, request, abort
import uuid
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


def _fetch_package(release_id, package_id):
    """
    Fetch a package, and validate it is part of the release
    """

    rq = db.session.query(DbRelease).filter(DbRelease.id == release_id)
    pq = db.session.query(DbPackage).filter(DbPackage.id == package_id)
    dbRelease = rq.first()
    dbPackage = pq.first()

    if not dbRelease:
        raise InvalidUsage("Release does not exist")
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

    app.logger.info('Release notes: %s, references: %s, platforms: %s',
                    release.notes, release.references, release.platforms)
    app.logger.info('Started release: %s', release.id)

    release.start()

    db.session.add(release)
    db.session.commit()

    return jsonify(id=release.id)


@app.route('/releases/<id>/packages', methods=['POST'])
def post_packages(id):
    _validate_package_input(request, id)

    app.logger.info(
        'Releasing package name: %s and version: %s, for release: %s',
        request.json['name'],
        request.json['version'], id)

    dbPackage = _create_package(id, request)

    app.logger.info('Package id: %s', str(dbPackage.id))
    db.session.add(dbPackage)
    db.session.commit()

    return jsonify(id=dbPackage.id)


@app.route('/releases/<release_id>/packages/<package_id>/results',
           methods=['POST'])
def post_results(release_id, package_id):
    dbResults = DbResults(package_id, str(request.json))
    db.session.add(dbResults)
    db.session.commit()
    return '', 204


@app.route('/releases/<release_id>/packages/<package_id>/start',
           methods=['POST'])
def post_package_start(release_id, package_id):
    """
    Indicate that a package has started deploying
    """
    dbPackage = _fetch_package(release_id, package_id)
    dbPackage.start()

    db.session.add(dbPackage)
    db.session.commit()
    return '', 204


@app.route('/releases/<release_id>/packages/<package_id>/stop',
           methods=['POST'])
def post_package_stop(release_id, package_id):
    """
    Indicate that a package has finished deploying
    """
    success = request.json['success']
    dbPackage = _fetch_package(release_id, package_id)
    dbPackage.stop(success=success)

    db.session.add(dbPackage)
    db.session.commit()
    return '', 204
