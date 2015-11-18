from __future__ import print_function, unicode_literals
from datetime import datetime, timedelta
import orlo
import json
import uuid
from flask.ext.testing import TestCase
from orlo.orm import db, DbPackage, DbRelease
from orlo.config import config


class OrloTest(TestCase):
    """
    Base class for tests which contains the methods required to move
    releases and packages through the workflow
    """

    def create_app(self):
        app = orlo.app
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
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

    def _create_release(self,
                        user='testuser',
                        team='test team',
                        platforms='test_platform',
                        references='TestTicket-123',
                        ):
        """
        Create a release using the REST API

        :param user:
        :param team:
        :param platforms:
        :param reference:
        :return: the release ID
        """

        response = self.client.post(
            '/releases',
            data=json.dumps({
                'note': 'test note lorem ipsum',
                'platforms': platforms,
                'references': references,
                'team': team,
                'user': user,
            }),
            content_type='application/json',
        )
        self.assert200(response)
        return response.json['id']

    def _create_package(self, release_id,
                        name='test-package',
                        version='1.2.3',
                        diff_url=None,
                        rollback=False,
                        ):
        """
        Create a package using the REST API

        :param release_id: release id to create the package for
        :param name:
        :param version:
        :param diff_url:
        :param rollback:
        :return: package id
        """
        doc = {
            'name': name,
            'version': version,
        }

        if diff_url:
            doc['diff_url'] = diff_url
        if rollback:
            doc['rollback'] = rollback

        response = self.client.post(
            '/releases/{}/packages'.format(release_id),
            data=json.dumps(doc),
            content_type='application/json',
        )
        self.assert200(response)
        return response.json['id']

    def _start_package(self, release_id, package_id):
        """
        Start a package using the REST API

        :param release_id:
        :return:
        """

        response = self.client.post(
            '/releases/{}/packages/{}/start'.format(release_id, package_id),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 204)
        return response

    def _stop_package(self, release_id, package_id,
                      success=True):
        """
        Start a package using the REST API

        :param release_id:
        :return:
        """

        response = self.client.post(
            '/releases/{}/packages/{}/stop'.format(release_id, package_id),
            data=json.dumps({
                'success': str(success),
                'foo': 'bar',
            }),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 204)
        return response

    def _stop_release(self, release_id):
        """
        Stop a release using the REST API

        :param release_id:
        :return:
        """
        response = self.client.post(
            '/releases/{}/stop'.format(release_id),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 204)
        return response

    def _create_finished_release(self):
        """
        Create a completed release, with default values, that has gone through
        the whole workflow
        """
        release_id = self._create_release()
        package_id = self._create_package(release_id)

        self._start_package(release_id, package_id)
        self._stop_package(release_id, package_id)
        self._stop_release(release_id)

        return release_id


class PostContractTest(OrloTest):
    """
    Test the HTTP POST contract
    """

    def test_create_release(self):
        """
        Create a release
        """
        release_id = self._create_release()
        self.assertEqual(uuid.UUID(release_id).get_version(), 4)

    def test_create_package(self):
        """
        Create a package
        """
        release_id = self._create_release()
        package_id = self._create_package(release_id)
        self.assertEqual(uuid.UUID(package_id).get_version(), 4)

    def test_add_results(self):
        """
        Add the results of a package deploy
        """
        release_id = self._create_release()
        package_id = self._create_package(release_id)

        results_response = self.client.post(
            '/releases/{}/packages/{}/results'.format(
                release_id, package_id),
            data=json.dumps({
                'success': 'true',
                'foo': 'bar',
            }),
            content_type='application/json',
        )
        self.assertEqual(results_response.status_code, 204)

    def test_package_start(self):
        """
        Test starting a package
        """
        release_id = self._create_release()
        package_id = self._create_package(release_id)

        return release_id, package_id

    def test_package_stop(self):
        """
        Test stopping a package
        """
        release_id = self._create_release()
        package_id = self._create_package(release_id)
        self._start_package(release_id, package_id)
        self._stop_package(release_id, package_id)

    def test_release_stop(self):
        """
        Test stopping a release

        As before, calls all the others as we need a full workflow present
        """
        release_id = self._create_release()
        package_id = self._create_package(release_id)
        self._start_package(release_id, package_id)
        self._stop_package(release_id, package_id)
        self._stop_release(release_id)

    def test_create_release_minimal(self):
        """
        Create a release, omitting all optional parameters
        """
        response = self.client.post('/releases',
            data=json.dumps({
                'platforms': ['test_platform'],
                'user': 'testuser',
            }),
            content_type='application/json',
        )
        self.assert200(response)

    def test_diffurl_present(self):
        """
        Test that the diff_url parameter is stored
        """
        test_url = 'http://example.com'

        release_id = self._create_release()
        package_id = self._create_package(release_id, diff_url=test_url)

        q = db.session.query(DbPackage).filter(DbPackage.id == package_id)
        pkg = q.first()
        self.assertEqual(pkg.diff_url, test_url)

    def test_rollback_present(self):
        """
        Test that that rollback parameter is stored
        """
        release_id = self._create_release()
        package_id = self._create_package(release_id, rollback=True)

        q = db.session.query(DbPackage).filter(DbPackage.id == package_id)
        pkg = q.first()

        self.assertEqual(pkg.rollback, True)


class GetContractTest(OrloTest):
    """
    Test the HTTP GET contract
    """

    def _get_releases(self, release_id=None, filters=None):
        """
        Perform a GET to /releases with optional filters
        """

        if release_id:
            path = '/releases/{}'.format(release_id)
        elif filters:
            path = '/releases?{}'.format('&'.join(filters))
        else:
            path = '/releases'

        print("GET {}".format(path))
        results_response = self.client.get(
            path, content_type='application/json',
        )
        self.assertEqual(results_response.status_code, 200)
        r_json = json.loads(results_response.data)
        return r_json

    def test_ping(self):
        """
        Start with something simple
        """
        response = self.client.get('/ping')
        self.assert200(response)
        self.assertEqual(response.data, 'pong')

    def test_get_single_release(self):
        """
        Fetch a single release
        """
        release_id = self._create_release()
        r = self._get_releases(release_id=release_id)

        self.assertEqual(1, len(r['releases']))
        self.assertEqual(release_id, r['releases'][0]['id'])

    def test_get_releases(self):
        """
        Test the list of releases
        """
        for _ in range(0, 3):
            self._create_finished_release()
        results = self._get_releases()
        self.assertEqual(len(results['releases']), 3)

    def test_get_release_filter_package(self):
        """
        Filter on releases that contain a package
        """
        for _ in range(0, 3):
            self._create_finished_release()

        release_id = self._create_release()
        package_id = self._create_package(release_id, name='specific-package')
        results = self._get_releases(filters=[
            'package_name=specific-package'
            ])

        for r in results['releases']:
            for p in r['packages']:
                self.assertEqual(p['name'], 'specific-package')
                self.assertEqual(p['id'], package_id)

        self.assertEqual(len(results['releases']), 1)

    def test_get_release_filter_user(self):
        """
        Filter on releases that were performed by a user
        """
        for _ in range(0, 3):
            self._create_release(user='firstUser')

        for _ in range(0, 2):
            self._create_release(user='secondUser')

        first_results = self._get_releases(filters=['user=firstUser'])
        second_results = self._get_releases(filters=['user=secondUser'])

        self.assertEqual(len(first_results['releases']), 3)
        self.assertEqual(len(second_results['releases']), 2)

        for r in first_results['releases']:
            self.assertEqual(r['user'], 'firstUser')
        for r in second_results['releases']:
            self.assertEqual(r['user'], 'secondUser')

    def test_get_release_filter_platform(self):
        """
        Filter on releases that were on a particular platform
        """
        for _ in range(0, 3):
            self._create_release(platforms='firstPlatform')

        for _ in range(0, 2):
            self._create_release(platforms=['firstPlatform', 'secondPlatform'])

        first_results = self._get_releases(filters=['platform=firstPlatform'])
        second_results = self._get_releases(filters=['platform=secondPlatform'])

        # Should be all releases
        self.assertEqual(len(first_results['releases']), 5)
        # Just those that contain "secondPlatform"
        self.assertEqual(len(second_results['releases']), 2)

        for r in first_results['releases']:
            self.assertIn('firstPlatform', r['platforms'])
        for r in second_results['releases']:
            self.assertIn('secondPlatform', r['platforms'])

    def _get_releases_time_filter(self, field, finished=False):
        """
        Return releases given the time-based filter field

        Abstracts a bit of common code in the stime/ftime tests
        """
        for _ in range(0, 3):
            if finished:
                self._create_finished_release()
            else:
                self._create_release()

        t_format = config.get('main', 'time_format')
        now = datetime.utcnow()

        yesterday = (now - timedelta(days=1)).strftime(t_format)
        tomorrow = (now + timedelta(days=1)).strftime(t_format)

        r_yesterday = self._get_releases(filters=['{}={}'.format(field, yesterday)])
        r_tomorrow = self._get_releases(filters=['{}={}'.format(field, tomorrow)])

        return r_yesterday, r_tomorrow

    def test_get_release_filter_stime_before(self):
        """
        Filter on releases that started before a particular time
        """
        r_yesterday, r_tomorrow = self._get_releases_time_filter('stime_before')

        self.assertEqual(3, len(r_tomorrow['releases']))
        self.assertEqual(0, len(r_yesterday['releases']))

    def test_get_release_filter_stime_after(self):
        """
        Filter on releases that started after a particular time
        """
        r_yesterday, r_tomorrow = self._get_releases_time_filter('stime_after')

        self.assertEqual(0, len(r_tomorrow['releases']))
        self.assertEqual(3, len(r_yesterday['releases']))

    def test_get_release_filter_ftime_before(self):
        """
        Filter on releases that finished before a particular time
        """
        r_yesterday, r_tomorrow = self._get_releases_time_filter(
            'ftime_before', finished=True)

        self.assertEqual(3, len(r_tomorrow['releases']))
        self.assertEqual(0, len(r_yesterday['releases']))

    def test_get_release_filter_ftime_after(self):
        """
        Filter on releases that finished after a particular time
        """
        r_yesterday, r_tomorrow = self._get_releases_time_filter(
            'ftime_after', finished=True)

        self.assertEqual(0, len(r_tomorrow['releases']))
        self.assertEqual(3, len(r_yesterday['releases']))

    def test_get_release_filter_duration_less(self):
        """
        Filter on releases that took less than x seconds

        All releases take a very small amount of time in our tests,
        but all should be <10 and >0 at least!
        """
        for _ in range(0, 3):
            self._create_finished_release()

        r = self._get_releases(filters=['duration_less=10'])
        self.assertEqual(3, len(r['releases']))

        r = self._get_releases(filters=['duration_less=0'])
        self.assertEqual(0, len(r['releases']))

    def test_get_release_filter_duration_greater(self):
        """
        Filter on releases that took greater than x seconds
        """
        for _ in range(0, 3):
            self._create_finished_release()

        r = self._get_releases(filters=['duration_greater=10'])
        self.assertEqual(0, len(r['releases']))

        r = self._get_releases(filters=['duration_greater=0'])
        self.assertEqual(3, len(r['releases']))

    def test_get_release_filter_team(self):
        """
        Filter on releases that a team was responsible for
        """
        for _ in range(0, 3):
            self._create_release(team='firstTeam')

        for _ in range(0, 2):
            self._create_release(team='secondTeam')

        first_results = self._get_releases(filters=['team=firstTeam'])
        second_results = self._get_releases(filters=['team=secondTeam'])

        self.assertEqual(len(first_results['releases']), 3)
        self.assertEqual(len(second_results['releases']), 2)

        for r in first_results['releases']:
            self.assertEqual(r['team'], 'firstTeam')
        for r in second_results['releases']:
            self.assertEqual(r['team'], 'secondTeam')
