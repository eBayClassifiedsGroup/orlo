from __future__ import print_function, unicode_literals
import json

__author__ = 'alforbes'


def string_to_list(string):
    """
    Load a list from a string

    :param string:
    :return:
    """
    if string is None:
        return []

    if '[' in string and \
            ']' in string and \
            ('"' in string or "'" in string):
        # Valid list syntax, presumably
        return json.loads(string.replace("'", '"'))
    else:
        # assume just one item
        return [string]


def list_to_string(array):
    """
    Convert a list to a string for storage in the DB

    :param array:
    :return:
    """
    if not array:
        return []

    return '["' + '", "'.join(array) + '"]'
