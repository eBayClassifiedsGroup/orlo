from __future__ import print_function
import json
import subprocess
from threading import Timer
from orlo.config import config
from orlo.exceptions import OrloDeployError
from orlo import app

__author__ = 'alforbes'


class BaseDeploy(object):
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


class HttpDeploy(BaseDeploy):
    """
    A http-based Deployment
    """

    def __init__(self, release):
        super(HttpDeploy, self).__init__(release)

    def start(self):
        pass

    def kill(self):
        raise NotImplementedError("No kill method for HTTP deploys")


class ShellDeploy(BaseDeploy):
    """
    Deployment by shell command

    Data is passed to the shell command given in 3 ways:

    * ORLO_URL, ORLO_RELEASE (the ID), and other Release attributes
      are set as environment variables (all prefixed by ORLO_)
    * The package and version sets are passed as arguments, e.g.
      package-name=1.0.0
    * The metadata dictionary is passed to stdin
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
        app.logger.debug("Args: {}".format(str(args)))

        env = {
            'ORLO_URL': self.server_url,
            'ORLO_RELEASE': str(self.release.id)
        }
        for key, value in self.release.to_dict().items():
            my_key = "ORLO_" + key.upper()
            env[my_key] = json.dumps(value)

        app.logger.debug("Env: {}".format(json.dumps(env)))

        metadata = {}
        for m in self.release.metadata:
            metadata.update(m.to_dict())
        in_data = json.dumps(metadata)

        return self.run_command(
            args, env, in_data, timeout_sec=config.getint('deploy', 'timeout'))

    def kill(self):
        """
        Kill a deploy in progress
        """
        raise NotImplementedError

    @staticmethod
    def run_command(args, env, in_data, timeout_sec=3600):
        """
        Run a command in a separate thread

        Adapted from http://stackoverflow.com/questions/1191374

        :param env: Dict of environment variables
        :param in_data: String to pass to stdin
        :param list args: Arguments (i.e. full list including command,
        as you would pass to subprocess)
        :param timeout_sec: Timeout in seconds, 1 hour by default
        :return:
        """
        try:
            proc = subprocess.Popen(
                args,
                env=env,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except OSError as e:
            raise OrloDeployError(
                message="OSError starting process: {}".format(
                    e.strerror),
                payload={'arguments': args}
            )

        timer = Timer(timeout_sec, proc.kill)
        out = err = " "
        try:
            timer.start()
            out, err = proc.communicate(in_data.encode('utf-8'))
        finally:
            timer.cancel()
            app.logger.debug("Out:\n{}".format(out))
            app.logger.debug("Err:\n{}".format(err))

        if proc.returncode is not 0:
            raise OrloDeployError(
                message="Subprocess exited with code {}".format(
                    proc.returncode),
                payload={
                    'stdout': out,
                    'stderr': err,
                },
                status_code=500)
        else:
            app.logger.info(
                "Deploy completed successfully. Output:\n{}".format(out))
        app.logger.debug("end run")

        return {
            'stdout': out,
            'stderr': err,
        }
