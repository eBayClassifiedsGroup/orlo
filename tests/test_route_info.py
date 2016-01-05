from __future__ import print_function
from tests.test_contract import OrloHttpTest

__author__ = 'alforbes'


class OrloInfoUrlTest(OrloHttpTest):
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

    def test_info_packages(self):
        """
        Test /info/packages
        """

        self._create_finished_release()
        response = self.client.get('/info/packages')
        self.assert200(response)
        self.assertIn('test-package', response.json)

    def test_info_package_list(self):
        """
        Test /info/package_list
        """

        self._create_finished_release()
        response = self.client.get('/info/packages/list')
        self.assert200(response)
        self.assertIn('test-package', response.json['packages'])

    def test_info_package_versions(self):
        """
        Test /info/packages returns 200
        """
        self._create_finished_release()
        response = self.client.get('/info/packages/versions')
        self.assert200(response)
        self.assertIn('test-package', response.json)

    def test_info_package_versions_with_platform(self):
        """
        Test /info/packages returns 200
        """
        self._create_finished_release()
        response = self.client.get('/info/packages/versions/test_platform')
        self.assert200(response)
        self.assertIn('test-package', response.json)

    def test_info_package_versions_with_platform_negative(self):
        """
        Test /info/packages returns 200
        """
        self._create_finished_release()
        response = self.client.get('/info/packages/versions/non-existent-platform')
        self.assert200(response)
        self.assertNotIn('test-package', response.json)
