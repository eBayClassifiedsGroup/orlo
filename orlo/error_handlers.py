from __future__ import print_function
from flask import jsonify, request
from orlo import app
from orlo.exceptions import InvalidUsage, OrloError

__author__ = 'alforbes'


@app.errorhandler(404)
def page_not_found(error):
    d = {'message': "404 Not Found", 'url': request.url}
    return jsonify(d), 404


@app.errorhandler(OrloError)
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


