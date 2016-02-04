from __future__ import print_function
import ConfigParser
__author__ = 'alforbes'

config = ConfigParser.ConfigParser()

config.add_section('main')
config.set('main', 'debug_mode', 'false')
config.set('main', 'propagate_exceptions', 'true')
config.set('main', 'time_format', '%Y-%m-%dT%H:%M:%SZ')
config.set('main', 'time_zone', 'UTC')
config.set('main', 'strict_slashes', 'false')

config.add_section('db')
config.set('db', 'uri', 'postgres://orlo:password@localhost:5432/orlo')
config.set('db', 'echo_queries', 'false')

config.add_section('logging')
config.set('logging', 'debug', 'false')
config.set('logging', 'file', 'disabled')

config.read('/etc/orlo/orlo.ini')
