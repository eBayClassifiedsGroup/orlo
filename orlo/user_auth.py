from orlo import app
from orlo.config import config
from orlo.exceptions import OrloAuthError
from flask_httpauth import HTTPBasicAuth
from flask_tokenauth import TokenAuth, TokenManager
from flask import request, jsonify, g, make_response
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import (TimedJSONWebSignatureSerializer
                          as Serializer, BadSignature, SignatureExpired)
from functools import update_wrapper, wraps
import ldap


# initialization
user_auth = HTTPBasicAuth()
token_auth = TokenAuth(config.get('security', 'secret_key'))
token_manager = TokenManager(secret_key=config.get('security', 'secret_key'))


class conditional_auth(object):
    """
    Decorator which wraps a decorator, to only apply it if auth is enabled
    """
    def __init__(self, decorator):
        self.decorator = decorator
        update_wrapper(self, decorator)

    def __call__(self, func):
        """
        Call method
        """
        @wraps(func)
        def wrapped(*args, **kwargs):
            """
            Wrapped method
            """
            if config.getboolean('security', 'enabled'):
                app.logger.debug("Security enabled")
                return self.decorator(func)(*args, **kwargs)
            else:
                app.logger.debug("Security disabled")
                return func(*args, **kwargs)
        return wrapped


class User(object):
    def __init__(self, username, password):
        self.username = username
        self.password_hash = self.hash_password(password)
        self.confirmed = False

    def hash_password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        rc = check_password_hash(self.password_hash, password)
        return rc

    def generate_auth_token(self, expiration=3600):
        secret_key = config.get('security', 'secret_key')
        s = Serializer(secret_key, expires_in=expiration)
        return s.dumps({'id': self.username})

    @staticmethod
    def verify_auth_token(token):
        app.logger.debug("Verify auth token called")
        s = Serializer(config.get('security', 'secret_key'))
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None  # valid token, but expired
        except BadSignature:
            return None  # invalid token
        user = data['id']
        return user


@user_auth.verify_password
def verify_password(username_or_token=None, password=None):
    # first try to authenticate by token
    user = User.verify_auth_token(username_or_token)
    if user:
        set_current_user_as(user)
        return True
    elif not user:
        password_file_user = verify_password_file(username_or_token, password)
        if password_file_user:
            set_current_user_as(username_or_token)
            return True
        else:
            ldap_user = verify_ldap_access(username_or_token, password)
            if ldap_user:
                set_current_user_as(username_or_token)
                return True
            else:
                return False


@token_auth.verify_token
def verify_token(token=None):
    app.logger.debug("Verify token called")
    if not token:
        return False
    token_user = token_manager.verify(token)
    if token_user:
        set_current_user_as(token_user)
        return True


def set_current_user_as(user):
    if not g.get('current_user'):
        app.logger.debug('Setting current user to: {}'.format(user))
        g.current_user = user


def verify_ldap_access(username, password):
    app.logger.debug("Verify ldap called")
    try:
        ldap_server = config.get('security', 'ldap_server')
        ldap_port = config.get('security', 'ldap_port')
        user_base_dn = config.get('security', 'user_base_dn')
        l = ldap.initialize('ldap://{}:{}'.format(ldap_server, ldap_port))
        ldap_user = "uid=%s,%s" % (username, user_base_dn)
        l.protocol_version = ldap.VERSION3
        l.simple_bind_s(ldap_user, password)
        return True
    except ldap.LDAPError:
        return False


def verify_password_file(username=None, password=None):
    app.logger.debug("Verify password file called")
    password_file = config.get('security', 'passwd_file')
    with open(password_file) as f:
        for line in f:
            line = line.strip()
            user = line.split(':')[0]
            if not user == username:
                continue
            # found user return password
            elif user == username:
                app.logger.debug("Found user {} in file".format(username))
                pw = ':'.join(line.split(':')[1:])
                checked_password = check_password_hash(pw, password)
                if checked_password:
                    return True
                else:
                    return False


@user_auth.error_handler
@token_auth.error_handler
def auth_error():
    """
    Authentication error
    """
    response = jsonify({'error': 'not authorized'})
    response.status_code = 401
    return response


@app.route('/token')
@conditional_auth(user_auth.login_required)
def get_token():
    """
    Get a token
    """
    ttl = config.getint('security', 'token_ttl')
    token = token_manager.generate(g.current_user, ttl)
    return jsonify({
        'token': token.decode('ascii'),
        'duration': config.get('security', 'token_ttl')
    })
