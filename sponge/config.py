from __future__ import print_function
import ConfigParser
__author__ = 'alforbes'

config = ConfigParser.ConfigParser()

config.add_section('main')
config.add_section('db')
config.add_section('logging')

config.set('main', 'propagate_exceptions', 'true')

config.set('db', 'uri', 'sqlite://')

config.set('logging', 'debug', 'true')
config.set('logging', 'file', 'disabled')

config.read('/etc/sponge.ini')
