from orlo import app
from flask import request, jsonify, g
from flask.ext.httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import (TimedJSONWebSignatureSerializer
                          as Serializer, BadSignature, SignatureExpired)

# initialization
app.config['SECRET_KEY'] = 'Who lives in a pineapple under the sea?'
app.debug = True

# extensions
auth = HTTPBasicAuth()


class User(object):

    def __init__(self, name):
        self.name = name
        self.password_hash = self.getpwent(name)
        self.confirmed = False

    def getpwent(self, name):
        with open('etc/passwd') as f:
            for line in f:
                line = line.strip()
                user = line.split(':')[0]
                if not user == name:
                    continue

                # found user return password
                pw = ':'.join(line.split(':')[1:])
                return pw

        # user not in passwd file return a hash that cannot occur
        return '*'

    def hash_password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        rc = check_password_hash(self.password_hash, password)
        return rc

    def generate_auth_token(self, expiration=600):
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


@auth.verify_password
def verify_password(username=None, password=None):
    user = None
    try:
        token = request.headers.get('X-Auth-Token').strip()
        user = User.verify_auth_token(token)
    except:
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


@auth.error_handler
def auth_error():
    response = jsonify({'error': 'not authorized'})
    response.status_code = 401
    return response


@app.before_request
@auth.login_required
def before_request():
    if not g.current_user.confirmed:
        response = jsonify({'error': 'not authorized'})
        response.status_code = 401
        return response


@app.route('/token')
@auth.login_required
def get_token():
    token = g.current_user.generate_auth_token(600)
    return jsonify({'token': token.decode('ascii'), 'duration': 600})


if __name__ == '__main__':
    pass
