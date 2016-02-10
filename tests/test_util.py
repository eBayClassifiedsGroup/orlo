from __future__ import print_function
from unittest import TestCase
import orlo.util

__author__ = 'alforbes'


class TestUtil(TestCase):
    def test_str_to_bool_true(self):
        """
        Test some values for True
        """
        for v in ['true', 'TrUE', '1', 't', '99', 1, 99]:
            self.assertIs(orlo.util.str_to_bool(v), True)

    def test_str_to_bool_false(self):
        """
        Test some values for True
        """
        for v in ['false', 'FaLsE', 'f', '0', '-99', 0, -99]:
            self.assertIs(orlo.util.str_to_bool(v), False)
