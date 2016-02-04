import os
from orlo import app
from flask import abort, request, jsonify, g, url_for
from flask.ext.httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
from passlib.apps import custom_app_context as pwd_context
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
        rc =  check_password_hash(self.password_hash, password)
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
def verify_password(username = None, password=None):
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
        # return forbidden('Unconfirmed account')
    

@app.route('/auth/users', methods=['POST'])
def new_user():
    username = request.json.get('username')
    password = request.json.get('password')
    if username is None or password is None:
        abort(400)  # missing arguments
    if User.query.filter_by(username=username).first() is not None:
        abort(400)  # existing user
    user = User(username=username)
    user.hash_password(password)
    db.session.add(user)
    db.session.commit()
    return (jsonify({'username': user.username}), 201,
            {'Location': url_for('get_user', id=user.id, _external=True)})


@app.route('/auth/users/<int:id>')
def get_user(id):
    user = User.query.get(id)
    if not user:
        abort(400)
    return jsonify({'username': user.username})

@app.route('/token')
@auth.login_required
def get_token():
    token = g.current_user.generate_auth_token(600)
    return jsonify({'token': token.decode('ascii'), 'duration': 600})

@app.route('/auth/token')
@auth.login_required
def get_auth_token():
    token = g.user.generate_auth_token(600)
    return jsonify({'token': token.decode('ascii'), 'duration': 600})


@app.route('/auth/resource')
@auth.login_required
def get_resource():
    return jsonify({'data': 'Hello, %s!' % g.user.username})


if __name__ == '__main__':
    if not os.path.exists('db.sqlite'):
        db.create_all()
    app.run(debug=True)
