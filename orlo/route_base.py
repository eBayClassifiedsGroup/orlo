from __future__ import print_function
from flask import jsonify, request
from orlo import app
from orlo import __version__

__author__ = 'alforbes'

"""
Base application routes and general functions
"""


@app.before_request
def log_post_data():
    """
    Before each request, log any POST data, without newlines
    """
    s = "{m} {u}".format(m=request.method, u=request.url)
    data = request.get_data(as_text=True)
    if data:
        s += " POST data: {}".format(data.replace('\n', ''))
    app.logger.info(s)


@app.route('/', methods=['GET'])
def root():
    """
    Root page, display info
    """
    return jsonify({
        'message': "Orlo server, see http://orlo.readthedocs.org/"
    })


@app.route('/version', methods=['GET'])
def version():
    """
    Display version information
    :return:
    """
    return jsonify({
        'version': str(__version__)
    })


@app.route('/ping', methods=['GET'])
def ping():
    """
    Simple ping test, takes no parameters

    **Example curl**:

    .. sourcecode:: shell

        curl -X GET 'http://127.0.0.1/ping'
    """
    return jsonify({
        'message': 'pong'
    })
