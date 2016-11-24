from __future__ import print_function

import logging
import os
import traceback

import alembic
import alembic.util.exc as alembic_exc
import sqlalchemy.exc
from logging.handlers import RotatingFileHandler
from flask_alembic import alembic_script
from flask_script import Manager, Command, Option, Server
from orlo.config import config
from orlo.app import app, OrloApplication
from orlo.orm import db


logger = logging.getLogger('orlo')

__author__ = 'alforbes'


class Start(Command):
    """
    Run the Gunicorn API server
    """

    option_list = (
        Option('-l', '--loglevel', default=config.get('logging', 'level'),
               help='Set logging level, config means use what\'s in config '
                    'file API:gunicorn_loglevel',
               choices=['debug', 'info', 'warning', 'error', 'critical']),
        Option('-c', '--log-console', default=False, dest='console',
               action='store_true',
               help="Log to console instead of configured log files"),
        Option('--workers', default=config.get('gunicorn', 'workers'),
               help="Number of gunicorn workers to start"),
    )

    def run(self, loglevel, console, workers):
        """
        Start the production server

        @param loglevel:
        @param console:
        @return:
        """
        log_level = getattr(logging, loglevel.upper())
        logger.setLevel(log_level)

        formatter = logging.Formatter(
            config.get('logging', 'format', raw=True))

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

        if console:
            # Stream handler should use configured log level
            stream_handler.setLevel(log_level)
        else:
            # Only print critical errors from now on
            stream_handler.setLevel(logging.CRITICAL)

        # File logging
        log_dir = config.get('logging', 'directory')
        if '/' in log_dir:
            file_handler = RotatingFileHandler(
                os.path.join('log_dir', 'app.log'))
            file_handler.setFormatter(formatter)
            file_handler.setLevel(log_level)
            logger.addHandler(file_handler)

        logger.debug('Debug logging enabled')

        gunicorn_options = {
            'accesslog': config.get('API', 'gunicorn_accesslog') if not
            console else '-',
            'bind': '%s:%s' % ('0.0.0.0', '5000'),
            'capture_output': True,
            'errorlog': config.get('API', 'gunicorn_errorlog') if not
            console else '-',
            'logfile': config.get('API', 'gunicorn_logfile') if not
            console else '-',
            'loglevel': loglevel or config.get('API', 'gunicorn_loglevel'),
            'on_exit': on_exit,
            'on_starting': on_starting,
            'workers': workers or config.get('API', 'gunicorn_workers'),
        }
        try:
            OrloApplication(app, gunicorn_options).run()
        except KeyboardInterrupt:
            logger.info('Caught KeyboardInterrupt')
        logger.debug('__main__ done')


class WriteConfig(Command):
    option_list = (
        Option('file', dest='file_path', help='Config file to write',
               default='/etc/orlo/orlo.ini')
    )

    def run(self, file_path):
        """ Write out configuration """
        config_file = open(file_path, 'w')
        config.write(config_file)


script_manager = Manager(app)
script_manager.add_command('db', alembic_script)
script_manager.add_command('start', Start)
script_manager.add_command('run_dev_server', Server(host='0.0.0.0', port=5000))


def on_starting(server):
    """ Start our managers """
    logger.debug('on_starting called')
    check_database()


def on_exit(server):
    logger.debug('on_exit called')


def check_database():
    logger.debug('Checking database "{}"'.format(
        config.get('API', 'db_uri')
    ))

    try:
        with app.app_context():
            current_head = alembic.script_directory.get_current_head()
            current_rev = alembic.migration_context.get_current_revision()
            logger.debug('Current revision: {}'.format(current_rev))
            logger.debug('Current head: {}'.format(current_head))
            if current_head is None:
                logger.warning('No alembic revisions, initialising')
                alembic.revision('Initial revision')
                alembic.upgrade()
            elif current_rev is None:
                logger.info('Database not configured, calling alembic upgrade')
                alembic.upgrade()
            elif current_rev != current_head:
                logger.info('New database revision available, calling alembic '
                            'upgrade')
                alembic.upgrade()
    except sqlalchemy.exc.OperationalError:
        logger.warning('Database is not configured, creating tables')
        db.create_all()
    except alembic_exc.CommandError:
        logger.error(
            'Alembic raised an exception, please check the state of the '
            'database, and that there aren\'t any extra files in '
            '/opt/venvs/gumtree-deployer/local/lib/python2.7/site-packages'
            '/gumtreeDeployer/rest/migrations. Exception '
            'was:\n{}'.format(traceback.format_exc()))
        raise SystemExit(1)

    logger.info('Database is configured')


def main():
    """
    Entry point for setuptools to call
    """
    try:
        script_manager.run()
    except StandardError:
        # Should print here as there is no guarantee logging is working
        tb = traceback.format_exc()
        print('Exception on execution:\n{}'.format(tb))


if __name__ == "__main__":
    main()
