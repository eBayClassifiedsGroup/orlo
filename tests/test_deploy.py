from __future__ import print_function
from tests import OrloLiveTest
from tests.test_orm import OrloDbTest
import orlo
from orlo.deploy import Deploy, HttpDeploy, ShellDeploy
from orlo.orm import db, Release

__author__ = 'alforbes'


class DeployTest(OrloLiveTest, OrloDbTest):
    """
    Test the Deploy class
    """
    CLASS = Deploy

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
        self.assertIsInstance(o, Deploy)


class BaseDeployTest(DeployTest):
    def test_not_implemented(self):
        """
        Base Deploy class should raise NotImplementedError on start
        """
        o = self.CLASS(self.release)
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
    CLASS = ShellDeploy

    def test_start(self):
        """
        Test that start emits a shell command
        :return:
        """
        deploy = ShellDeploy(self.release)
        deploy.start()

    def test_kill(self):
        """
        Test that kill emits a shell command
        :return:
        """
        pass
