from __future__ import print_function, division, absolute_import
from __future__ import unicode_literals
from pkg_resources import get_distribution

__version__ = get_distribution(__name__).version

from orlo.config import config
from orlo.app import app as app


app.logger.info("Initialisation completed")
