from __future__ import print_function, unicode_literals
import json
from orlo import app
from orlo.orm import db, Release, Package, Platform
from orlo.exceptions import InvalidUsage
from sqlalchemy.orm import exc

__author__ = 'alforbes'


def create_release(request):
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


def create_package(release_id, request):
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


def fetch_release(release_id):
    """
    Fetch a release by ID
    """
    rq = db.session.query(Release).filter(Release.id == release_id)
    release = rq.first()
    if not release:
        raise InvalidUsage("Release does not exist")
    return release


def fetch_package(release_id, package_id):
    """
    Fetch a package, and validate it is part of the release
    """

    # Fetch release first, as it is a good sanity check
    fetch_release(release_id)
    pq = db.session.query(Package).filter(Package.id == package_id)
    package = pq.first()

    if not package:
        raise InvalidUsage("Package does not exist")
    if str(package.release_id) != release_id:
        raise InvalidUsage("This package does not belong to this release")

    return package


def validate_request_json(request):
    try:
        request.json
    except Exception:
        # This is pretty ugly, but we want something more user friendly than "Bad Request"
        raise InvalidUsage("Could not parse JSON document")

    if not request.json:
        raise InvalidUsage('Missing application/json header', status_code=400)


def validate_release_input(request):
    validate_request_json(request)
    if 'platforms' not in request.json:
        raise InvalidUsage('JSON doc missing platforms field', status_code=400)
    return True


def validate_package_input(request, release_id):
    validate_request_json(request)

    if not 'name' in request.json or not 'version' in request.json:
        raise InvalidUsage("Missing name / version in request body.")
    app.logger.debug("Package request validated, release_id {}".format(release_id))
    return True


def _validate_package_stop_input(request):
    validate_request_json(request)
    if 'success' not in request.json:
        raise InvalidUsage("Missing success key in JSON doc")



def list_to_string(array):
    """
    Convert a list to a string for storage in the DB

    :param array:
    :return:
    """
    if not array:
        return []

    return '["' + '", "'.join(array) + '"]'
