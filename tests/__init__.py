import orlo
import unittest
from orlo.orm import db
from flask.ext.testing import TestCase, LiveServerTestCase


class OrloTest(TestCase):
    """
    Base test class to setup the app
    """
    def create_app(self):
        app = orlo.app
        app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://orlo:password@localhost:5432/orlo'
        # app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
        app.config['TESTING'] = True
        app.config['DEBUG'] = True
        app.config['TRAP_HTTP_EXCEPTIONS'] = True
        app.config['PRESERVE_CONTEXT_ON_EXCEPTION'] = False

        return orlo.app

    def setUp(self):
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()


class OrloLiveTest(LiveServerTestCase):
    """
    Test on a live server
    """

    def create_app(self):
        app = orlo.app
        app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://orlo:password@localhost:5432/orlo'
        # app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
        app.config['TESTING'] = True
        app.config['DEBUG'] = True
        app.config['TRAP_HTTP_EXCEPTIONS'] = True
        app.config['PRESERVE_CONTEXT_ON_EXCEPTION'] = False

        return orlo.app

    def setUp(self):
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
