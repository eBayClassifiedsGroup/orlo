from flask import Flask
from logging.handlers import RotatingFileHandler

from orlo.config import config

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = config.get('db', 'uri')

if config.getboolean('main', 'propagate_exceptions'):
    app.config['PROPAGATE_EXCEPTIONS'] = True

if config.getboolean('logging', 'debug'):
    app.debug = True
app.logger.debug('Debug enabled')

if not config.getboolean('main', 'strict_slashes'):
    app.url_map.strict_slashes = False

logfile = config.get('logging', 'file')
if logfile != 'disabled':
    handler = RotatingFileHandler(
        logfile,
        maxBytes=10000,
        backupCount=1,
    )
    app.logger.addHandler(handler)

# Must be imported last
import orlo.error_handlers
import orlo.route_api
import orlo.route_import

