from __future__ import print_function
from flask import jsonify
from orlo.app import app
from orlo import __version__

__author__ = 'alforbes'


@app.route('/internal/version', methods=['GET'])
def internal_version():
    """
    Get the running version of Orlo
    :return:
    """
    return jsonify({'version': __version__})
