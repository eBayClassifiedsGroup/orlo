from orlo import app
from orlo.config import config
from orlo.exceptions import OrloAuthError
from flask.ext.httpauth import HTTPBasicAuth
from flask_tokenauth import TokenAuth
from flask import request, jsonify, g, make_response
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import (TimedJSONWebSignatureSerializer
                          as Serializer, BadSignature, SignatureExpired)
from functools import wraps

# initialization

user_auth = HTTPBasicAuth()
token_auth = TokenAuth(config.get('security', 'secret_key'))


class User(object):
    def __init__(self, name):
        self.name = name
        self.password_hash = self.get_pw_ent(name)
        self.confirmed = False

    @staticmethod
    def get_pw_ent(name):
        if config.get('security', 'method') == 'file':
            with open(config.get('security', 'passwd_file')) as f:
                for line in f:
                    line = line.strip()
                    user = line.split(':')[0]
                    if not user == name:
                        continue

                    # found user return password
                    app.logger.debug("Found user {} in file".format(name))
                    pw = ':'.join(line.split(':')[1:])
                    return pw
            # user not in passwd file return a hash that cannot occur
            return '*'

        # TODO implement LDAP
        raise OrloAuthError("Unknown user_auth method, check security config")

    def hash_password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        rc = check_password_hash(self.password_hash, password)
        return rc

    def generate_auth_token(self, expiration=3600):
        s = Serializer(app.config['SECRET_KEY'], expires_in=expiration)
        return s.dumps({'id': self.name})

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None  # valid token, but expired
        except BadSignature:
            return None  # invalid token
        name = data['id']
        return User(name)


@user_auth.verify_password
def verify_password(username=None, password=None):
    if not config.getboolean('security', 'enabled'):
        return True

    user = None
    try:
        token = request.headers.get('X-Auth-Token').strip()
        user = User.verify_auth_token(token)
    except:  # TODO be more specific here
        pass

    if user:
        g.current_user = user
        g.current_user.confirmed = True
        return True

    # try to authenticate with username/password
    if not password:
        return False

    user = User(username)
    if not user.verify_password(password):
        return False

    g.current_user = user
    g.current_user.confirmed = True
    return True


@user_auth.error_handler
@token_auth.error_handler
def auth_error():
    """
    Authentication error
    """
    # raise OrloAuthError("Not authorized")
    response = jsonify({'error': 'not authorized foo'})
    response.status_code = 401
    return response


@app.before_request
def before_request():
    """
    Check the user is authenticated
    """
    if config.getboolean('security', 'enabled') \
            and request.endpoint != 'get_token':
        try:
            if not g.current_user.confirmed:
                raise OrloAuthError("Not authenticated for endpoint {}".format(
                    request.endpoint))
        except AttributeError:
            # current_user is not set
            raise OrloAuthError("Not authenticated")


@app.route('/token')
@user_auth.login_required
def get_token():
    """
    Get a token
    """
    ttl = config.getint('security', 'token_ttl')
    token = g.current_user.generate_auth_token(ttl)

    return jsonify({
        'token': token.decode('ascii'),
        'duration': config.get('security', 'token_ttl')
    })

