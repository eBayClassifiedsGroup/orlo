from __future__ import print_function
from test_orm import OrloDbTest
from test_base import ReleaseDbUtil
from flask_testing import LiveServerTestCase
from orlo.orm import db
import orlo
import requests
import os

__author__ = 'alforbes'

try:
    TRAVIS = True if os.environ['TRAVIS'] == 'true' else False
except KeyError:
    TRAVIS = False


class StressTest(LiveServerTestCase, ReleaseDbUtil):
    """ This test was to track down a database connection leak

    It stands because it detected the leak by stalling on db.drop_all() in
    the tearDown function
    """
    ITERATIONS = 1

    def create_app(self):
        if TRAVIS:
            db_uri = 'postgres://orlo:password@localhost:5432/orlo'
        else:
            db_uri = 'postgres://orlo:password@192.168.57.100:5432/orlo'

        app = orlo.app
        app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
        # app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
        app.config['TESTING'] = True
        app.config['DEBUG'] = False
        app.config['TRAP_HTTP_EXCEPTIONS'] = True
        app.config['PRESERVE_CONTEXT_ON_EXCEPTION'] = False
        app.config['LIVESERVER_PORT'] = 8943
        app.config['LIVESERVER_TIMEOUT'] = 5

        return orlo.app

    def setUp(self):
        db.get_engine(self.app).dispose()
        db.create_all()
        db.session.begin_nested()

    def tearDown(self):
        db.session.rollback()
        db.session.close()
        db.drop_all()  # stall here implies connection leak
        db.session.remove()
        db.get_engine(self.app).dispose()

    def _get_releases(self, release_id=None, filters=None, expected_status=200):
        """
        Perform a GET to /releases with optional filters
        """

        if release_id:
            path = '{}/releases/{}'.format(self.get_server_url(),
                                           release_id)
        elif filters:
            path = '{}/releases?{}'.format(self.get_server_url(),
                                           '&'.join(filters))
        else:
            path = '{}/releases'.format(self.get_server_url())

        results_response = requests.get(
            path, headers={'content_type': 'application/json'}
        )

        self.assertEqual(results_response.status_code, expected_status)
        return results_response.json

    def test_hammer_postgres(self):
        """ Hammer postgres and see if it times out """
        for i in range(0, self.ITERATIONS):
            if i+1 % 50 == 0:
                print('Creating release {}'.format(i+1))
            OrloDbTest._create_finished_release(success=True)

        for i in range(0, self.ITERATIONS):
            print('get', i)
            self._get_releases(filters=['user=testuser'])

