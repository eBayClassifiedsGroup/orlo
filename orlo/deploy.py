from __future__ import print_function

__author__ = 'alforbes'


class Deploy(object):
    """
    A Deploy task

    Deploy tasks are simpler than releases, as they consist of just packages
    and versions. The backend deployer is responsible for creating Orlo Releases
    via the REST API.

    Integrations can either sub-class Deploy and override the start method and
    (optionally) the kill method, or use the pre-built shell and http
    integrations.
    """

    def __init__(self, package_doc, metadata=None):
        """
        :dict package_doc: a dict of packages to be released, e.g.
            {package1: version, package2: version}
        :dict metadata: an optional dictionary of metadata which is passed to
            the deployer
        """

        self.package_doc = package_doc
        self.metadata = metadata

    def start(self):
        """
        Start the deployment
        """
        raise NotImplementedError("Please override the start method")

    def kill(self):
        """
        Kill a deployment in progress
        """
        raise NotImplementedError("Please override the kill method")


class HttpDeploy(Deploy):
    """
    A http-based Deployment
    """
    def __init__(self, package_doc, base_url):
        super(HttpDeploy, self).__init__(package_doc)
        self.base_url = base_url

    def start(self):
        pass

    def kill(self):
        pass


class ShellDeploy(Deploy):
    """
    Deployment by shell command

    meta {} => stdin
    deployer pkg1=1
    capture stdout,

    env USER, TEAM, URL, REFERENCES, (ORLO_
    """
    def __init__(self, package_doc, command):
        super(ShellDeploy, self).__init__(package_doc)
        self.command = command

    def start(self):
        """

        :return:
        """
        pass

    def kill(self):
        pass
