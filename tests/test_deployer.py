from __future__ import print_function
import unittest

"""
Test the example deployer
"""


class TestDeployer(unittest.TestCase):
    ENV = {}
    ARGS = {}
    METADATA = {}

    def test_exit_0(self):
        """
        Test the deployer exits 0
        """