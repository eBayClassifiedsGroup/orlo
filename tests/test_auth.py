from __future__ import print_function
from flask.ext.testing import TestCase
from flask import jsonify
import orlo
from orlo.orm import db
from orlo.user_auth import user_auth, token_auth, conditional_auth
from tests import ConfigChange
from werkzeug.datastructures import Headers
from werkzeug.test import Client
import base64

__author__ = 'alforbes'

USER = 'testuser'
PASSWORD = 'blah'


# A couple of test routes which require auth, and return 200 if it succeeds
@orlo.app.route('/test/token_required')
@conditional_auth(token_auth.token_required)
def token_required():
    response = jsonify({'message': 'OK'})
    response.status_code = 200
    return response


@orlo.app.route('/test/auth_required')
@conditional_auth(user_auth.login_required)
def auth_required():
    response = jsonify({'message': 'OK'})
    response.status_code = 200
    return response


class OrloAuthTest(TestCase):
    """
    Base test class to setup the app
    """
    def create_app(self):
        self.app = orlo.app
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
        self.app.config['TESTING'] = True
        self.app.config['DEBUG'] = True
        self.app.config['TRAP_HTTP_EXCEPTIONS'] = True
        self.app.config['PRESERVE_CONTEXT_ON_EXCEPTION'] = False

        return self.app

    def setUp(self):
        db.create_all()
        self.orig_security_enabled = orlo.config.get('security', 'enabled')
        self.orig_security_method = orlo.config.get('security', 'method')
        orlo.config.set('security', 'enabled', 'true')
        orlo.config.set('security', 'method', 'file')

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        orlo.config.set('security', 'enabled', self.orig_security_enabled)
        orlo.config.set('security', 'method', self.orig_security_method)

    def get_with_basic_auth(self, path, username='testuser', password='blabla'):
        """
        Do a request with basic auth

        :param path:
        :param username:
        :param password:
        """
        h = Headers()
        h.add('Authorization', 'Basic ' + base64.b64encode(
            '{u}:{p}'.format(u=username, p=password)
        ))
        response = Client.open(self.client, path=path, headers=h)
        return response

    def get_with_token_auth(self, path, token):
        """
        Do a request with token auth

        :param token:
        :param path:
        """
        h = Headers()
        h.add('X-Auth-Token', token)
        response = Client.open(self.client, path=path, headers=h)
        return response

    def post_with_token_auth(self, path, token, data):
        """
        Do a request with token auth

        :param token:
        :param path:
        """
        h = Headers()
        h.add('X-Auth-Token', token)
        h.add('Content-Type', 'application/json')
        response = Client.open(self.client, method='POST', data=data, path=path, headers=h)
        return response

    def get_token(self):
        response = self.get_with_basic_auth('/token')
        return response.json['token']


class TestOrloAuthToken(OrloAuthTest):
    def test_token(self):
        """
        Test that we can fetch a token
        """
        response = self.get_with_basic_auth('/token')
        self.assert200(response)
        self.assertIn('token', response.json)


class TestTokenAuth(OrloAuthTest):
    """
    Parent class for testing Token authentication
    """
    URL_PATH = '/test/token_required'

    def test_unauthorised(self):
        """
        Test that we get 401 without a token
        """
        response = self.client.get(self.URL_PATH)
        self.assert401(response)

    def test_auth_disabled(self):
        """
        Same test as above with auth disabled
        """
        with ConfigChange('security', 'enabled', 'false'):
            response = self.client.get(self.URL_PATH)
            self.assert200(response)

    def test_with_token(self):
        token = self.get_token()
        response = self.get_with_token_auth(self.URL_PATH, token)
        self.assert200(response)

    def test_with_bad_token(self):
        token = 'foo'
        response = self.get_with_token_auth(self.URL_PATH, token)
        self.assert401(response)


class TestUserAuth(OrloAuthTest):
    """
    Parent class for testing HTTP Basic authentication
    """
    URL_PATH = '/test/auth_required'

    def test_auth_disabled(self):
        """
        Same test as above with auth disabled
        """
        with ConfigChange('security', 'enabled', 'false'):
            response = self.client.get(self.URL_PATH)
            self.assert200(response)

    def test_with_login(self):
        response = self.get_with_basic_auth('/test/auth_required')
        self.assert200(response)

    def test_with_bad_login(self):
        response = self.get_with_basic_auth(
            '/test/auth_required', username='bad_user', password='foobar'
        )
        self.assert401(response)


class TestReleasesAuth(OrloAuthTest):
    """
    Test auth against a real url, /releases

    Bit more complicated as we have to do some POST requests
    """
    URL_PATH = '/releases'

    def test_get_returns_200(self):
        """
        No auth required for GETs
        """
        url = self.URL_PATH + '?platform=foo'
        response = self.client.get(url)
        self.assert200(response)

    def test_post_releases_returns_401(self):
        """
        Test auth fails
        """
        response = self.client.post(self.URL_PATH, data={'foo': 'bar'})
        self.assert401(response)

    def test_post_releases_with_token_returns_400(self):
        """
        Test auth succeeds
        """
        token = self.get_token()
        response = self.post_with_token_auth(
            self.URL_PATH, token=token, data={'foo': 'bar'},
        )
        self.assert400(response)
        self.assertIn('message', response.data)
