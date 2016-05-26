from __future__ import print_function
import logging
import sys

__author__ = 'alforbes'


class OrloError(Exception):
    status_code = 500

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


class InvalidUsage(OrloError):
    status_code = 400


class DatabaseError(OrloError):
    status_code = 500


class OrloWorkflowError(OrloError):
    status_code = 400


class OrloAuthError(OrloError):
    status_code = 401


class OrloStartupError(Exception):
    def __init__(self, message):
        Exception.__init__(self)
        print("Startup Error: " + message)


class OrloConfigError(Exception):
    def __init__(self, message):
        Exception.__init__(self)
        print("Configuration Error: " + message)


class OrloDeployError(OrloError):
    status_code = 500
