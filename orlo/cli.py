from __future__ import print_function
import argparse

try:
    from orlo import __version__
except ImportError:
    # _version.py doesn't exist
    __version__ = "TEST_BUILD"


__author__ = 'alforbes'

"""
Command line interface

Generally setup/initialisation functions and the like, called by /usr/bin/orlo
"""


def parse_args():
    parser = argparse.ArgumentParser(prog='orlo')

    parser.add_argument('--version', '-v', action='version',
                        version='%(prog)s {}'.format(__version__))

    p_config = argparse.ArgumentParser(add_help=False)
    p_config.add_argument('--file', '-f', dest='file_path',
                          help="Config file to read/write",
                          default='/etc/orlo/orlo.ini')

    p_database = argparse.ArgumentParser(add_help=False)
    p_server = argparse.ArgumentParser(add_help=False)
    p_server.add_argument('--host', '-H', dest='host', default='127.0.0.1',
                          help="Address to listen on")
    p_server.add_argument('--port', '-P', dest='port', type=int, default=5000,
                          help="Port to listen on")

    subparsers = parser.add_subparsers(dest='action')
    sp_config = subparsers.add_parser(
            'write_config', help="Write config file",
            parents=[p_config])
    sp_config.set_defaults(func=write_config)

    sp_database = subparsers.add_parser(
            'setup_database', help="Initialise the configured DB",
            parents=[p_database, p_config])
    sp_database.set_defaults(func=setup_database)

    sp_run_server = subparsers.add_parser(
            'run_server', help="Run a test server",
            parents=[p_server, p_config])
    sp_run_server.set_defaults(func=run_server)

    return parser.parse_args()


def write_config(args):
    from orlo import config
    config_file = open(args.file_path, 'w')
    config.write(config_file)


def setup_database(args):
    from orlo.orm import db
    from orlo.config import config

    if config.get('db', 'uri') == 'sqlite://':
        print("Warning: setting up in-memory database, this is "
              "probably not what you want!\n"
              "Please configure db:uri in /etc/orlo/orlo.ini")
    db.create_all()


def run_server(args):
    print("Warning: this is a development server and not suitable "
          "for production, we recommend running under gunicorn.")

    from orlo import app
    app.config['DEBUG'] = True
    app.config['TRAP_HTTP_EXCEPTIONS'] = True
    app.config['PRESERVE_CONTEXT_ON_EXCEPTION'] = False
    app.run(host=args.host, port=args.port, debug=True, use_reloader=True)


def main():
    # Referenced by entry_points in setup.py
    args = parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
