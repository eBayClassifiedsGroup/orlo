from __future__ import print_function
from tests.test_contract import OrloHttpTest
from orlo.deploy import Deploy, HttpDeploy, ShellDeploy

__author__ = 'alforbes'


class DeployTest(OrloHttpTest):
    """
    Test the Deploy class
    """
    CLASS = Deploy
    PACKAGE_DOC = {
        'package_one': '1.0.0',
        'package_two': '2.0.0',
    }

    def test_init(self):
        """
        Test that we can instantiate the class
        """
        o = self.CLASS(self.PACKAGE_DOC)
        self.assertIsInstance(o, Deploy)


class BaseDeployTest(DeployTest):
    def test_not_implemented(self):
        """
        Base Deploy class should raise NotImplementedError on start
        """
        o = self.CLASS(self.PACKAGE_DOC)
        with self.assertRaises(NotImplementedError):
            o.start()


class HttpDeployTest(DeployTest):
    CLASS = HttpDeploy

    def test_start(self):
        """
        Test that start emits an http call
        """
        pass

    def test_kill(self):
        """
        Test that kill emits an http call
        """
        pass


class ShellDeployTest(DeployTest):
    CLASS = HttpDeploy

    def test_start(self):
        """
        Test that start emits a shell command
        :return:
        """
        pass

    def test_kill(self):
        """
        Test that kill emits a shell command
        :return:
        """
        pass
