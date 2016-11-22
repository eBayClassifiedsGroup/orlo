from __future__ import print_function
from test_base import OrloLiveTest, OrloTest, ConfigChange, ReleaseDbUtil
from orlo.deploy import BaseDeploy, HttpDeploy, ShellDeploy
from orlo.orm import db, Release, Package
from test_base import OrloLiveTest
from test_base import ReleaseDbUtil
import unittest

__author__ = 'alforbes'


class DeployTest(OrloLiveTest, ReleaseDbUtil):
    """
    Test the Deploy class
    """
    CLASS = BaseDeploy

    def setUp(self):
        super(DeployTest, self).setUp()
        rid = self._create_release()
        pid = self._create_package(rid)
        self.release = db.session.query(Release).first()

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

