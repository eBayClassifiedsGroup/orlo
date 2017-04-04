from __future__ import print_function
import os
from six.moves.configparser import RawConfigParser

__author__ = 'alforbes'


# Defaults that can be overridden by environment variables
defaults = {
    'ORLO_CONFIG': '/etc/orlo/orlo.ini',
    'ORLO_LOGDIR': '/var/log/orlo',
}

for var, default in defaults.items():
    try:
        defaults[var] = os.environ[var]
    except KeyError:
        pass

config = RawConfigParser()

config.add_section('main')
config.set('main', 'time_format', '%Y-%m-%dT%H:%M:%SZ')
config.set('main', 'time_zone', 'UTC')
config.set('main', 'strict_slashes', 'false')
config.set('main', 'base_url', 'http://localhost:8080')

config.add_section('gunicorn')
config.set('gunicorn', 'workers', '4')

config.add_section('security')
config.set('security', 'enabled', 'false')
config.set('security', 'passwd_file', 'none')
config.set('security', 'secret_key', 'change_me')
# NOTE: orlo.__init__ checks that secret_key is not "change_me" when security
# is enabled. Do not change the default here without updating __init__ as well.
config.set('security', 'token_ttl', '3600')
config.set('security', 'ldap_server', 'localhost.localdomain')
config.set('security', 'ldap_port', '389')
config.set('security', 'user_base_dn', 'ou=people,ou=example,o=test')

config.add_section('db')
config.set('db', 'uri', 'sqlite://')
config.set('db', 'echo_queries', 'false')
config.set('db', 'pool_size', '50')

config.add_section('flask')
config.set('flask', 'propagate_exceptions', 'true')
config.set('flask', 'debug', 'false')

config.add_section('logging')
config.set('logging', 'level', 'info')
config.set('logging', 'format', '%(asctime)s [%(name)s] %(levelname)s %('
                                'module)s:%(funcName)s:%(lineno)d - %('
                                'message)s')
config.set('logging', 'directory', defaults['ORLO_LOGDIR'])  # "disabled" for no
                                                          # log files

config.read(defaults['ORLO_CONFIG'])
