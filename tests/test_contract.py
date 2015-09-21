import sponge
from httplib import HTTPConnection
import json
import unittest
import uuid
from flask import Flask
from flask.ext.testing import LiveServerTestCase

HOST = 'localhost'
HEADERS = {'Content-Type': 'application/json'}

class ContractTest(LiveServerTestCase):
    def create_app(self):
        app = sponge.app
        app.config['TESTING'] = True
        app.config['LIVESERVER_PORT'] = 7767
        return app


    def test_create_release(self):
        response, release = self._create_release(
                platforms=['poop'],
                references=[],
                notes='')
        self.assertEqual(response.status, 200)
        self.assertEqual(uuid.UUID(release['id']).get_version(), 4)


    def test_create_package(self):
        release_response, release = self._create_release(
                platforms=['poop'])
        package_response, package = self._create_package(
                release,
                name='somepkg',
                version='someversion')
        self.assertEqual(package_response.status, 200)
        self.assertEqual(uuid.UUID(package['id']).get_version(), 4)


    def test_add_results(self):
        release_response, release = self._create_release(
                platforms=['stuffs']
                )
        package_response, package = self._create_package(
                release,
                name='someotherpkg',
                version='42')
        url = "/release/%s/packages/%s/results" % (release['id'], package['id'])
        conn = self.__connect()
        try:
            conn.request('POST', url, '{}', HEADERS)
            response = conn.getresponse()
            self.assertEqual(204, response.status)
        finally:
            conn.close()


    def _create_release(self, **args):
        conn = self.__connect()
        try:
            print(json.dumps(args))
            conn.request('POST', '/release', json.dumps(args), HEADERS)
            response = conn.getresponse()
            return (response, json.loads(response.read()))
        finally:
            conn.close()


    def _create_package(self, release, **args):
        url = "/release/%s/packages" % release['id']
        conn = self.__connect()
        try:
            conn.request('POST', url, json.dumps(args), HEADERS)
            response = conn.getresponse()
            return (response, json.loads(response.read()))
        finally:
            conn.close()

    def __connect(self):
        return HTTPConnection(HOST, self.port)
