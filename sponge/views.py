from sponge import app
from flask import jsonify, request, abort
import uuid
from datetime import datetime
from orm import db, DbRelease, DbPackage, DbResults


class InvalidUsage(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv


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


def _validate_release_input(request):
    if not request.json:
        raise(InvalidUsage('Missing application/json header', status_code=400))
    if 'platforms' not in request.json:
        raise(InvalidUsage('JSON doc missing platforms field', status_code=400))


def _package_input_is_valid(request, id):
    if not request.json:
        app.logger.error("Missing JSON body.")
        return False

    if not 'name' in request.json or not 'version' in request.json:
        app.logger.error("Missing name / version in request body.")
        return False

    return True


@app.route('/ping', methods=['GET'])
def ping():
    return 'pong'


@app.route('/release', methods=['POST'])
def post_release():
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


@app.route('/release/<id>/packages', methods=['POST'])
def post_packages(id):
    if not _package_input_is_valid(request, id):
        raise InvalidUsage("Input not valid")

    app.logger.info(
        'Releasing package name: %s and version: %s, for release: %s',
        request.json['name'],
        request.json['version'], id)

    dbPackage = _create_package(id, request)

    app.logger.info('Package id: %s', str(dbPackage.id))
    dbPackage.start()
    db.session.add(dbPackage)
    db.session.commit()

    return jsonify(id=dbPackage.id)


@app.route('/release/<release_id>/packages/<package_id>/results',
           methods=['POST'])
def post_results(release_id, package_id):
    dbResults = DbResults(package_id, str(request.json))
    db.session.add(dbResults)
    db.session.commit()
    return ('', 204)
