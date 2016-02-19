from flask import Flask
import logging
from logging.handlers import RotatingFileHandler

from orlo.config import config
from orlo.exceptions import OrloStartupError
from orlo._version import __version__

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = config.get('db', 'uri')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

if config.getboolean('main', 'propagate_exceptions'):
    app.config['PROPAGATE_EXCEPTIONS'] = True

if config.getboolean('db', 'echo_queries'):
    app.config['SQLALCHEMY_ECHO'] = True

# Debug mode ignores all custom logging and should only be used in
# local testing...
if config.getboolean('main', 'debug_mode'):
    app.debug = True

# ...as opposed to loglevel debug, which can be used anywhere
if config.getboolean('logging', 'debug'):
    app.logger.setLevel(logging.DEBUG)

app.logger.debug('Debug enabled')

if not config.getboolean('main', 'strict_slashes'):
    app.url_map.strict_slashes = False

logfile = config.get('logging', 'file')
if logfile != 'disabled':
    handler = RotatingFileHandler(
        logfile,
        maxBytes=1048576,
        backupCount=1,
    )
    app.logger.addHandler(handler)

if config.getboolean('security', 'enabled') and \
        config.get('security', 'secret_key') == 'change_me':
    raise OrloStartupError("Security is enabled, please configure the secret key")


# Must be imported last
import orlo.error_handlers
import orlo.route_base
import orlo.route_releases
import orlo.route_import
import orlo.route_info
import orlo.route_stats
import orlo.user_auth

