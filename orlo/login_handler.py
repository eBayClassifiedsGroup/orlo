from __future__ import print_function
from flask.ext.httpauth import HTTPBasicAuth
from functools import wraps
from orlo import config

__author__ = 'alforbes'


class OrloHTTPBasicAuth(HTTPBasicAuth):
    """
    Subclass to override the log_required decorator
    """

    def login_required(self, func):
        """
        Checks that authentication is enabled before applying the decorator

        If security is enabled, we apply the decorator of the parent.

        :param func: Function to decorate
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            if config.getboolean('security', 'enabled'):
                executed = super(OrloHTTPBasicAuth, self).\
                    login_required(func)
            else:
                # Just execute the function
                executed = func
            return executed(*args, **kwargs)
        return wrapper
