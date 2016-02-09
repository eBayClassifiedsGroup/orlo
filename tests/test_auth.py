from __future__ import print_function
from flask.ext.testing import TestCase
import orlo
from orlo.orm import db
from tests import ConfigChange
from werkzeug.datastructures import Headers
from werkzeug.test import Client
import base64

__author__ = 'alforbes'

orlo.config.set('security', 'enabled', 'true')
orlo.config.set('security', 'method', 'file')
USER = 'testuser'
PASSWORD = 'blah'


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

    def tearDown(self):
        db.session.remove()
        db.drop_all()

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


class TestOrloAuth(OrloAuthTest):
    URL_PATH = '/ping'

    def test_unauthorised(self):
        """
        Test that we get 401 without a token
        """
        response = self.client.get(self.URL_PATH)
        self.assert401(response)
        print(response.headers)

    def test_auth_disabled(self):
        """
        Same test as above with auth disabled
        """
        with ConfigChange('security', 'enabled', 'false'):
            response = self.client.get(self.URL_PATH)
            self.assert200(response)

    def test_auth_with_token(self):
        token = self.get_token()
        response = self.get_with_token_auth(self.URL_PATH, token)
        self.assert200(response)


class TestOrloAuthReleases(TestOrloAuth):
    """
    We probably don't want to apply the same blanket auth rules to all
    endpoints
    """
    URL_PATH = '/releases?platform=foo'
