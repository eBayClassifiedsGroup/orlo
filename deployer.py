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
                        help="Packages to deploy, in format package_name=version, "
                             "e.g test-package=1.0.0")
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
    orlo_client.package_start(package)

    # Do the deploy...

    # Determining success status is up to you
    success = True

    orlo_client.package_stop(package, success=success)

    return success


if __name__ == "__main__":
    if os.getenv('ORLO_URL'):
        orlo_url = os.environ['ORLO_URL']
    else:
        # This deployer is only every supposed to accept releases from Orlo
        # Other deployers could use this to detect whether they are being invoked by Orlo
        raise DeployerError("Could not detect ORLO_URL from environment")

    if os.getenv('ORLO_RELEASE'):
        orlo_release = os.environ['ORLO_RELEASE']
    else:
        raise DeployerError("Could not detect ORLO_RELEASE in environment")

    packages, metadata = get_params()

    orlo_client = OrloClient(uri=orlo_url)
    # The release is created in Orlo before being handed to the deployer
    # So fetch it here
    release = orlo_client.get_release(orlo_release)

    # Create packages from arguments if specified on the CLI,
    # otherwise fetch from the Orlo release
    orlo_packages = []
    if packages:
        for p, v in packages.items():
            info("Creating Package {}:{}".format(p, v))
            pkg = orlo_client.create_package(release, p, v)
            orlo_packages.append(pkg)
    elif release.packages:
        # Fetch from Orlo
        info("Fetching packages from Orlo")
        orlo_packages = release.packages
    else:
        raise DeployerError("No packages to deploy!")

    info("Starting Release")
    for pkg in orlo_packages:
        info("Deploying {}".format(pkg.name))
        deploy(pkg, meta=metadata)
    info("Finishing Release")

    orlo_client.release_stop(release)
    info("Done.")
