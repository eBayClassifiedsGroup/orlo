from __future__ import print_function
from flask import jsonify, request, Response, json, g
from orlo.app import app
from orlo import queries
from orlo.exceptions import InvalidUsage
from orlo.user_auth import token_auth
from orlo.orm import db, Release, Package, PackageResult, ReleaseNote, \
    ReleaseMetadata, Platform
from orlo.util import validate_request_json, create_release, \
    validate_release_input, validate_package_input, fetch_release, \
    create_package, fetch_package, stream_json_list, str_to_bool, is_uuid
from orlo.user_auth import conditional_auth

__author__ = 'alforbes'


"""
Note - the /packages/ endpoint is very alpha, it is not part of the usual
release workflow and intended for utilitarian uses such as debugging and
fixing errors.
"""


@app.route('/packages', methods=['GET'])
@app.route('/packages/<package_id>', methods=['GET'])
def get_packages(package_id=None):
    """
    Return a list of packages to the client

    :param package_id:
    :return:
    """

    booleans = ('rollback', )

    if package_id:  # Simple, just fetch one package
        if not is_uuid(package_id):
            raise InvalidUsage("Package ID given is not a valid UUID")
        query = queries.get_package(package_id)
    elif len([x for x in request.args.keys()]) == 0:
        raise InvalidUsage("Please specify a filter. See "
                           "http://orlo.readthedocs.org/en/latest/rest.html"
                           "#get--packages for more info")
    else:  # Bit more complex
        # Flatten args, as the ImmutableDict puts some values in a list when
        # expanded
        args = {}
        for k in request.args.keys():
            if k in booleans:
                args[k] = str_to_bool(request.args.get(k))
            else:
                args[k] = request.args.get(k)
        query = queries.packages(**args)

    # Execute eagerly to avoid confusing stack traces within the Response on
    # error
    db.session.execute(query)

    return Response(stream_json_list('packages', query),
                    content_type='application/json')
