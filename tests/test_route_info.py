from __future__ import print_function
from test_route_base import OrloHttpTest

__author__ = 'alforbes'


class TestInfoUrl(OrloHttpTest):
    def test_info_root(self):
        """
        Test /info returns 200
        """
        response = self.client.get('/info')
        self.assert200(response)

    def test_info_users(self):
        """
        Test /info/users returns 200
        """
        self._create_release(user='userOne')
        response = self.client.get('/info/users')
        self.assert200(response)
        self.assertIn('userOne', response.json)

    def test_info_users_with_user(self):
        """
        Test /info/users/username returns 200
        """
        self._create_release(user='userOne')
        response = self.client.get('/info/users/userOne')
        self.assert200(response)
        self.assertIn('userOne', response.json)

    def test_info_users_with_platform(self):
        """
        Test /info?platform=<platform> returns 200
        """
        self._create_release(user='userOne', platforms=['platformOne'])
        response = self.client.get('/info/users?platform=platformOne')
        self.assert200(response)
        self.assertIn('userOne', response.json)

    def test_info_platforms(self):
        """
        Test /info/platforms returns 200
        """
        self._create_release(platforms=['platformOne'])
        response = self.client.get('/info/platforms')
        self.assert200(response)
        self.assertIn('platformOne', response.json)

    def test_info_platforms_with_platform(self):
        """
        Test /info/platforms/<platform> returns 200
        """
        self._create_release(platforms=['platformOne'])
        response = self.client.get('/info/platforms/platformOne')
        self.assert200(response)
        self.assertIn('platformOne', response.json)

    def test_info_platforms_with_platform_negative(self):
        """
        Test /info/platforms/<platform> returns 200
        """
        self._create_release(platforms=['platformOne'])
        response = self.client.get('/info/platforms/badPlatform')
        self.assert200(response)
        self.assertNotIn('platformOne', response.json)

    def test_info_packages(self):
        """
        Test /info/packages
        """

        self._create_finished_release()
        response = self.client.get('/info/packages')
        self.assert200(response)
        self.assertIn('test-package', response.json)

    def test_info_packages_with_package(self):
        """
        Test /info/package with a package
        """
        rid = self._create_release()
        self._create_package(rid, name='packageOne')
        response = self.client.get('/info/packages/packageOne')
        self.assert200(response)
        self.assertIn('packageOne', response.json)

    def test_info_packages_with_platform(self):
        """
        Test /info/package with a platform filter
        """
        rid = self._create_release(platforms=['platformOne'])
        self._create_package(rid, name='packageOne')
        response = self.client.get('/info/packages?platform=platformOne')
        self.assert200(response)
        self.assertIn('packageOne', response.json)

    def test_info_packages_with_platform_negative(self):
        """
        Test /info/package with a platform filter
        """
        rid = self._create_release(platforms=['platformOne'])
        self._create_package(rid, name='packageOne')
        response = self.client.get('/info/packages?platform=platformFoo')
        self.assert200(response)
        self.assertNotIn('packageOne', response.json)

    def test_info_packages_list(self):
        """
        Test /info/package_list
        """

        self._create_finished_release()
        response = self.client.get('/info/packages/list')
        self.assert200(response)
        self.assertIn('test-package', response.json['packages'])

    def test_info_packages_list_with_platform(self):
        """
        Test /info/package_list
        """

        self._create_finished_release()
        response = self.client.get('/info/packages/list?platform=test_platform')
        self.assert200(response)
        self.assertIn('test-package', response.json['packages'])

    def test_info_packages_list_with_platform_negative(self):
        """
        Test /info/package_list
        """

        self._create_finished_release()
        response = self.client.get('/info/packages/list?platform=non-existent-platform')
        self.assert200(response)
        self.assertNotIn('test-package', response.json['packages'])

    def test_info_packages_versions(self):
        """
        Test /info/packages returns 200
        """
        self._create_finished_release()
        response = self.client.get('/info/packages/versions')
        self.assert200(response)
        self.assertIn('test-package', response.json)

    def test_info_packages_versions_with_platform(self):
        """
        Test /info/packages returns 200
        """
        self._create_finished_release()
        response = self.client.get('/info/packages/versions?platform=test_platform')
        self.assert200(response)
        self.assertIn('test-package', response.json)

    def test_info_package_versions_with_platform_negative(self):
        """
        Test /info/packages returns 200
        """
        self._create_finished_release()
        response = self.client.get('/info/packages/versions?platform=non-existent-platform')
        self.assert200(response)
        self.assertNotIn('test-package', response.json)
