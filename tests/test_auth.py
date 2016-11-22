from __future__ import print_function
from flask_testing import TestCase
from flask import jsonify
import orlo
from orlo.orm import db
from orlo.user_auth import user_auth, token_auth, conditional_auth
from test_base import ConfigChange
from werkzeug.datastructures import Headers
from werkzeug.test import Client
import base64
import ldap
from mockldap import MockLdap
import sys
if sys.version_info[0] < 3:
    from mock import patch
else:
    from unittest.mock import patch
from orlo.config import config

__author__ = 'alforbes'

USERNAME = 'testuser'
PASSWORD = 'blah'


config.set('security', 'passwd_file', '')


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


@orlo.app.route('/test/user')
@conditional_auth(user_auth.login_required)
def get_resource():
    return jsonify({'data': 'Hello, %s!' % g.current_user})


class OrloAuthTest(TestCase):
    """
    Base test class to setup the app
    """
    top = ('o=test', {'o': ['test']})
    example = ('ou=example,o=test', {'ou': ['example']})
    people = ('ou=people,ou=example,o=test', {'ou': ['other']})
    ldapuser = ('uid=ldapuser,ou=people,ou=example,o=test',
                {'uid': ['ldapuser'], 'userPassword': ['ldapuserpw']})
    # This is the content of our mock LDAP directory. It takes the form
    # {dn: {attr: [value, ...], ...}, ...}.
    directory = dict([top, example, people, ldapuser])

    def create_app(self):
        self.app = orlo.app
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
        self.app.config['TESTING'] = True
        self.app.config['DEBUG'] = False
        self.app.config['TRAP_HTTP_EXCEPTIONS'] = True
        self.app.config['PRESERVE_CONTEXT_ON_EXCEPTION'] = False

        return self.app

    @classmethod
    def setUpClass(self):
        # We only need to create the MockLdap instance once. The content we
        # pass in will be used for all LDAP connections.
        self.mockldap = MockLdap(self.directory)

    @classmethod
    def tearDownClass(self):
        del self.mockldap

    def setUp(self):
        db.create_all()
        self.mockldap.start()
        self.ldapobj = self.mockldap['ldap://localhost/']
        self.orig_security_enabled = orlo.config.get('security', 'enabled')
        self.orig_security_secret_key = orlo.config.set('security',
                                                        'secret_key')
        self.orig_security_ldap_server = orlo.config.set('security',
                                                         'ldap_server')
        self.orig_security_ldap_port = orlo.config.set('security', 'ldap_port')
        self.orig_security_user_base_dn = orlo.config.set('security',
                                                          'user_base_dn')
        orlo.config.set('security', 'enabled', 'true')
        orlo.config.set('security', 'secret_key', 'It does not matter how '
                                                  'slowly you go so long as '
                                                  'you do not stop')
        orlo.config.set('security', 'ldap_server', 'localhost')
        orlo.config.set('security', 'ldap_port', '389')
        orlo.config.set('security', 'user_base_dn',
                        'ou=people,ou=example,o=test')

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.mockldap.stop()
        del self.ldapobj
        orlo.config.set('security', 'enabled', self.orig_security_enabled)
        orlo.config.set('security', 'secret_key', self.orig_security_secret_key)

    def get_with_basic_auth(self, path, username='testuser', password='blah'):
        """
        Do a request with ldap auth

        :param path:
        :param username:
        :param password:
        """
        h = Headers()
        s_auth = base64.b64encode('{u}:{p}'.format(
            u=username, p=password).encode('utf-8'))
        h.add('Authorization', 'Basic ' + s_auth.decode('utf-8'))
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
        response = Client.open(self.client, method='POST', data=data, path=path,
                               headers=h)
        return response

    def get_token(self):
        response = self.get_with_basic_auth('/token')
        return response.json['token']


@patch('orlo.user_auth.verify_password_file')
class TestOrloAuthToken(OrloAuthTest):
    def test_fetch_token(self, mock_verify_password_file):
        """
        Test that we can fetch a token
        """
        mock_verify_password_file.return_value = True
        response = self.get_with_basic_auth('/token')
        self.assert200(response)
        self.assertIn('token', response.json)


@patch('orlo.user_auth.verify_password_file')
class TestTokenAuth(OrloAuthTest):
    """
    Parent class for testing Token authentication
    """
    URL_PATH = '/test/token_required'

    def test_unauthorised(self, mock_verify_password):
        """
        Test that we get 401 without a token
        """
        response = self.client.get(self.URL_PATH)
        self.assert401(response)

    def test_auth_disabled(self, mock_verify_password):
        """
        Same test as above with auth disabled
        """
        with ConfigChange('security', 'enabled', 'false'):
            response = self.client.get(self.URL_PATH)
            self.assert200(response)

    def test_with_token(self, mock_verify_password):
        token = self.get_token()
        response = self.get_with_token_auth(self.URL_PATH, token)
        self.assert200(response)

    def test_with_bad_token(self, mock_verify_password):
        token = 'foo'
        response = self.get_with_token_auth(self.URL_PATH, token)
        self.assert401(response)


@patch('orlo.user_auth.verify_password_file')
class TestUserAuth(OrloAuthTest):
    """
    Parent class for testing HTTP Basic authentication
    """
    URL_PATH = '/test/auth_required'

    def test_auth_disabled(self, mock_verify_password):
        """
        Same test as above with auth disabled
        """
        with ConfigChange('security', 'enabled', 'false'):
            response = self.client.get(self.URL_PATH)
            self.assert200(response)

    def test_with_login(self, mock_verify_password):
        response = self.get_with_basic_auth('/test/auth_required')
        self.assert200(response)

    def test_with_ldap_login(self, mock_verify_password):
        response = self.get_with_basic_auth(
            '/test/auth_required', username='ldapuser', password='ldapuserpw'
        )
        self.assert200(response)

    def test_with_bad_login(self, mock_verify_password):
        mock_verify_password.return_value = False
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

    @patch('orlo.user_auth.verify_password_file')
    def test_post_releases_with_token_returns_400(
            self, mock_verify_password_file):
        """
        Test auth succeeds
        """
        token = self.get_token()
        response = self.post_with_token_auth(
            self.URL_PATH, token=token, data={'foo': 'bar'},
        )
        self.assert400(response)
        self.assertIn(b'message', response.data)
