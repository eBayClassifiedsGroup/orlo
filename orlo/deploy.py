from __future__ import print_function
import subprocess
import json
from orlo.config import config
from orlo.exceptions import OrloError


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

    def __init__(self, release):
        """
        Perform a release
        """
        self.release = release
        self.server_url = config.get('main', 'base_url')

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
    def __init__(self, release):
        super(HttpDeploy, self).__init__(release)

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
    """
    def __init__(self, release):
        super(ShellDeploy, self).__init__(release)
        self.pid = None

    def start(self):
        """
        Start the deploy
        """
        args = [config.get('deploy_shell', 'command_path')]
        for p in self.release.packages:
            args.append("{}={}".format(p.name, p.version))
        print("Args: {}".format(str(args)))

        env = {
            'ORLO_URL': self.server_url
        }
        for key, value in self.release.to_dict().items():
            my_key = "ORLO_" + key.upper()
            env[my_key] = str(value)

        print("Env: {}".format(str(env)))
        p = subprocess.Popen(
            args,
            env=env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        metadata = {}
        for m in self.release.metadata:
            metadata.update(m.to_dict())
        #out, err = p.communicate(json.dumps(metadata))

        #print("Out:\n{}".format(out))
        #print("Err:\n{}".format(err))

        #if p.returncode is not 0:
        #    raise OrloError("Subprocess exited with code {}".format(
        #        p.returncode
        #    ))

    def kill(self):
        """
        Kill a deploy in progress
        """
        raise NotImplementedError