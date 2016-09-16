import orlo
import unittest
from orlo.orm import db
from flask_testing import TestCase, LiveServerTestCase


class OrloTest(TestCase):
    """
    Base test class to setup the app
    """
    def create_app(self):
        app = orlo.app
        app.config['SQLALCHEMY_DATABASE_URI'] = \
            'postgres://orlo:password@192.168.57.100:5432/orlo'
        # app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
        app.config['TESTING'] = True
        app.config['DEBUG'] = False
        app.config['TRAP_HTTP_EXCEPTIONS'] = True
        app.config['PRESERVE_CONTEXT_ON_EXCEPTION'] = False

        return orlo.app

    def setUp(self):
        db.create_all()
        db.session.begin_nested()

    def tearDown(self):
        db.session.rollback()
        db.session.remove()
        db.drop_all()


class OrloLiveTest(LiveServerTestCase):
    """
    Test on a live server
    """

    def create_app(self):
        app = orlo.app
        app.config['SQLALCHEMY_DATABASE_URI'] = \
            'postgres://orlo:password@192.168.57.100:5432/orlo'
        # app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
        app.config['TESTING'] = True
        app.config['DEBUG'] = False
        app.config['TRAP_HTTP_EXCEPTIONS'] = True
        app.config['PRESERVE_CONTEXT_ON_EXCEPTION'] = False

        return orlo.app

    def setUp(self):
        db.create_all()
        db.session.begin_nested()

    def tearDown(self):
        db.session.rollback()
        db.drop_all()
        db.session.remove()
        db.get_engine(self.app).dispose()


class ConfigChange(object):
    def __init__(self, section, option, value):
        """
        Decorator to temporarily change configuration

        @param section: ConfigParser section
        @param option: ConfigParser option
        @param value: Value to set
        @return:
        """
        self.section = section
        self.option = option
        self.value = value

    def __enter__(self):
        self.original_state = orlo.config.get(self.section, self.option)
        orlo.config.set(self.section, self.option, self.value)

    def __exit__(self, exc_type, exc_val, exc_tb):
        orlo.config.set(self.section, self.option, self.original_state)
