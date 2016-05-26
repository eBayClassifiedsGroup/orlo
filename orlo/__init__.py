from __future__ import print_function, division, absolute_import
from __future__ import unicode_literals
from flask import Flask
import logging
from logging.handlers import RotatingFileHandler
from logging import Formatter
import sys

from orlo.config import config, CONFIG_FILE
from orlo.exceptions import OrloStartupError, OrloError, OrloAuthError, \
    OrloConfigError

try:
    # _version is created by setup.py
    from orlo._version import __version__
except ImportError:
    __version__ = "TEST_BUILD"


app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = config.get('db', 'uri')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

if config.getboolean('main', 'propagate_exceptions'):
    app.config['PROPAGATE_EXCEPTIONS'] = True

if config.getboolean('db', 'echo_queries'):
    app.config['SQLALCHEMY_ECHO'] = True

if not config.getboolean('main', 'strict_slashes'):
    app.url_map.strict_slashes = False

# Debug mode ignores all custom logging and should only be used in
# local testing...
if config.getboolean('main', 'debug_mode'):
    app.debug = True

if not app.debug:
    log_level = config.get('logging', 'level')
    if log_level == 'debug':
        app.logger.setLevel(logging.DEBUG)
    elif log_level == 'info':
        app.logger.setLevel(logging.INFO)
    elif log_level == 'warning':
        app.logger.setLevel(logging.WARNING)
    elif log_level == 'error':
        app.logger.setLevel(logging.ERROR)

    logfile = config.get('logging', 'file')
    if logfile != 'disabled':
        file_handler = RotatingFileHandler(
            logfile,
            maxBytes=1048576,
            backupCount=1,
        )
        log_format = config.get('logging', 'format')
        formatter = Formatter(log_format)

        file_handler.setFormatter(formatter)
        app.logger.addHandler(file_handler)

if config.getboolean('security', 'enabled') and \
        config.get('security', 'secret_key') == 'change_me':
    raise OrloStartupError(
        "Security is enabled, please configure the secret key")

app.logger.debug("Log level: {}".format(config.get('logging', 'level')))

# Must be imported last
import orlo.error_handlers
import orlo.route_base
import orlo.route_releases
import orlo.route_import
import orlo.route_info
import orlo.route_stats
import orlo.user_auth

app.logger.info("Startup completed with configuration from {}".format(
    CONFIG_FILE))
