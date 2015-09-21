from __future__ import print_function

__author__ = 'alforbes'

from sponge import app
from sponge.orm import db

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sponge.db'
app.debug = True
db.create_all()


