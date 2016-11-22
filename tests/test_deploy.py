from __future__ import print_function
from test_base import OrloLiveTest, OrloTest, ConfigChange
from orlo.deploy import BaseDeploy, HttpDeploy, ShellDeploy
from orlo.orm import db, Release, Package
from orlo.util import append_or_create_platforms
import unittest

__author__ = 'alforbes'


class DeployTest(OrloLiveTest):
    """
    Test the Deploy class
    """
    CLASS = BaseDeploy

    def setUp(self):
        # super(DeployTest, self).setUp()
        db.create_all()
        rid = self._create_release()
        pid = self._create_package(rid)
        self.release = db.session.query(Release).first()

    @staticmethod
    def _create_release(user='testuser',
                        team='test team',
                        platforms=None,
                        references=None,
                        success=True):
        """
        Create a release using internal methods

        :param user:
        :param team:
        :param platforms:
        :param references:
        :return:
        """

        if not platforms:
            platforms = ['test_platform']
        if type(platforms) is not list:
            raise AssertionError("Platforms parameter must be list")
        if not references:
            references = ['TestTicket-123']

        db_platforms = append_or_create_platforms(platforms)

        r = Release(
            platforms=db_platforms,
            user=user,
            references=references,
            team=team,
        )
        db.session.add(r)
        db.session.commit()

        return r.id

    @staticmethod
    def _create_package(release_id,
                        name='test-package',
                        version='1.2.3',
                        diff_url=None,
                        rollback=False,
                        ):
        """
        Create a package using internal methods

        :param release_id:
        :param name:
        :param version:
        :param diff_url:
        :param rollback:
        :return:
        """
        p = Package(
            release_id=release_id,
            name=name,
            version=version,
            diff_url=diff_url,
            rollback=rollback,
        )
        db.session.add(p)
        db.session.commit()

        return p.id

    def test_init(self):
        """
        Test that we can instantiate the class
        """
        o = self.CLASS(self.release)
        self.assertIsInstance(o, BaseDeploy)


class TestBaseDeploy(DeployTest):
    def test_not_implemented(self):
        """
        Base Deploy class should raise NotImplementedError on start
        """
        o = self.CLASS(self.release)
        with self.assertRaises(NotImplementedError):
            o.start()


class TestHttpDeploy(DeployTest):
    CLASS = HttpDeploy

    @unittest.skip("Not implemented")
    def test_start(self):
        """
        Test that start emits an http call
        """
        pass

    @unittest.skip("Not implemented")
    def test_kill(self):
        """
        Test that kill emits an http call
        """
        pass


class TestShellDeploy(DeployTest):
    CLASS = ShellDeploy

    def test_start(self):
        """
        Test that start emits a shell command
        """
        with ConfigChange('deploy', 'timeout', '3'), \
                ConfigChange('deploy_shell', 'command_path', '/bin/true'):
            deploy = ShellDeploy(self.release)

            # Override server_url, normally it is set by config:
            deploy.server_url = self.get_server_url()

            deploy.start()

    @unittest.skip("Not implemented")
    def test_kill(self):
        """
        Test that kill emits a shell command
        """
        pass

    @unittest.skip("Doesn't work on travis")
    def test_start_example_deployer(self):
        """
        Test the example deployer completes

        DOESN'T WORK ON TRAVIS, as /bin/env python gives the system python
        """
        with ConfigChange('deploy', 'timeout', '3'):
            deploy = ShellDeploy(self.release)

            # Override server_url, normally it is set by config:
            deploy.server_url = self.get_server_url()

            deploy.start()

    def test_output(self):
        """
        Test that we return the output of the deploy

        Not a good test, as it relies on the test-package being an argument,
        and simply echoing it back. This is the "spec", but this test could
        break if the arguments change.
        """
        with ConfigChange('deploy', 'timeout', '3'), \
                ConfigChange('deploy_shell', 'command_path', '/bin/echo'):
            deploy = ShellDeploy(self.release)

            # Override server_url, normally it is set by config:
            deploy.server_url = self.get_server_url()

            output = deploy.start()
            self.assertEqual(output['stdout'], b'test-package=1.2.3\n')

