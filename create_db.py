from __future__ import print_function

__author__ = 'alforbes'

from orlo import app
from orlo.orm import db

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///orlo.db'
app.debug = True
db.create_all()


