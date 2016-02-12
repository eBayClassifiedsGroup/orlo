"""
flask_httpauth
==================

This module provides token-based authentication for Flask routes.

:copyright: (C) 2015 by Alex Forbes.
:license:   BSD, see LICENSE for more details.
"""
from __future__ import print_function
from itsdangerous import (TimedJSONWebSignatureSerializer
                          as Serializer, BadSignature, SignatureExpired)
from functools import wraps
from flask import request, make_response
from flask.ext.httpauth import HTTPAuth
from orlo import app

__author__ = 'alforbes'


class TokenAuthError(Exception):
    def __init__(self, message):
        Exception.__init__(self)
        self.message = message


class TokenManager(object):
    """ Create and verify Tokens
    """
    def __init__(self, secret_key):
        self.secret_key = secret_key

    def generate(self, name, expiration=3600):
        s = Serializer(self.secret_key, expires_in=expiration)
        return s.dumps({'id': name})

    def verify(self, token):
        s = Serializer(self.secret_key)
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None  # valid token, but expired
        except BadSignature:
            return None  # invalid token
        name = data['id']
        return name

    # Not finished
    def store(self, f):
        """ Optionally specify a function to store a token

        :param f:
        """
        raise NotImplementedError
        self.store_token_callback = f
        return f

    def retrieve(self, f):
        """ Optionally specify a function to retrieve a token
        :param f: Function to use
        """
        raise NotImplementedError
        self.retrieve_token_callback = f


class TokenAuth(object):
    """ Authenticate a token

    Takes X-Auth-Token header and extracts a user name value from it using a
    given TokenManager.

    Borrows heavily from Flask-HTTPAuth, many thanks to the authors!
    """
    def __init__(self, secret_key, realm=None):
        def default_error_handler():
            return "Access Denied"

        self.token_manager = TokenManager(secret_key=secret_key)
        self.realm = realm or "Authentication Token Required"

        self.verify_token(None)
        self.error_handler(default_error_handler)

    def error_handler(self, f):
        @wraps(f)
        def decorated(*args, **kwargs):
            res = f(*args, **kwargs)
            if type(res) == str:
                res = make_response(res)
                res.status_code = 401
            if 'WWW-Authenticate' not in res.headers.keys():
                res.headers['WWW-Authenticate'] = 'Token realm="{}"'.format(self.realm)
            return res
        self.auth_error_callback = decorated
        return decorated

    def token_required(self, f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = request.headers.get('X-Auth-Token')
            if not self.authenticate(token):
                return self.auth_error_callback()
            return f(*args, **kwargs)
        return decorated

    def authenticate(self, token):
        """ Authenticate a token

        :param token:
        """
        if self.verify_token:
            # Specified verify function overrides below
            return self.verify_token_callback(token)

        if not token:
            return False

        name = self.token_manager.verify(token)
        if not name:
            return False

        return True

    def verify_token(self, f):
        """ Optionally specify a function to perform the token verification

        For example, if it is present in a database.
        By default we just check we can decode it with our secret.

        :param f:
        """
        self.verify_token_callback = f
        return f

