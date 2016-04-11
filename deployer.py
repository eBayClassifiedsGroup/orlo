#!/usr/bin/env python
from __future__ import print_function
import argparse
import fileinput
import json
import logging
from collections import OrderedDict
from logging import error, warn, info
from orloclient import OrloClient, Release, Package
import os

__author__ = 'alforbes'

"""
An example deployer. This is used to run tests against, but could also be used
as a basis for Orlo integration.
"""

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


class DeployerError(Exception):
    def __init__(self, message):
        self.message = message
        error(message)


def get_params():
    parser = argparse.ArgumentParser(description="Orlo Test Deployer")
    parser.add_argument('packages', choices=None, const=None, nargs='*',
                        help="Packages to deploy, in format "
                             "package_name=version, e.g test-package=1.0.0")
    args, unknown = parser.parse_known_args()

    _packages = OrderedDict()

    for pkg in args.packages:
        package, version = pkg.split('=')
        _packages[package] = version

    # Fetch metadata from stdin
    s_metadata = ""
    for line in fileinput.input(unknown):
        s_metadata += line

    try:
        _metadata = json.loads(s_metadata)
    except ValueError:
        raise DeployerError("Could not parse json from stdin")

    return _packages, _metadata


def deploy(package, meta=None):
    """
    Dummy deployment function

    :param Package package: Package to deploy
    :param dict meta: Dictionary of metadata (unused in this dummy function)
    :return:
    """
    info("Package start - {}:{}".format(package.name, package.version))
    orlo_client.package_start(package)

    # Do stuff
    # Determining success status is up to you
    success = True

    info("Package stop - {}:{}".format(package.name, package.version))
    orlo_client.package_stop(package, success=success)

    return success


if __name__ == "__main__":
    if os.getenv('ORLO_URL'):
        orlo_url = os.environ['ORLO_URL']
    else:
        # This deployer is only every supposed to accept releases from Orlo
        # Other deployers could use this to detect whether they are being
        # invoked by Orlo
        raise DeployerError("Could not detect ORLO_URL from environment")

    if os.getenv('ORLO_RELEASE'):
        orlo_release_id = os.environ['ORLO_RELEASE']
    else:
        raise DeployerError("Could not detect ORLO_RELEASE in environment")

    logging.info(
        "Environment: \n" +
        json.dumps(os.environ, indent=2, default=lambda o: o.__dict__))

    # Fetch packages and metadata. Packages is not used, it is just to
    # demonstrate they are passed as arguments
    packages, metadata = get_params()

    logging.info("Stdin: \n" + str(metadata))

    # Create an instance of the Orlo client
    orlo_client = OrloClient(uri=orlo_url)

    # The release is created in Orlo before the deployer is invoked, so fetch
    # it here. If you prefer, you can to do the release creation within your
    # deployer and use Orlo only for receiving data
    release = orlo_client.get_release(orlo_release_id)

    # While we fetch Packages using the Orlo client, they are passed on the
    # CLI as well, which is useful for non-python deployers
    info("Fetching packages from Orlo")
    if not release.packages:
        raise DeployerError("No packages to deploy")

    info("Starting Release")
    for pkg in release.packages:
        info("Deploying {}".format(pkg.name))
        deploy(pkg, meta=metadata)

    info("Finishing Release")
    orlo_client.release_stop(release)

    info("Done.")
