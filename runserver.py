#!/usr/bin/env python
from orlo import app

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///orlo.db'

app.run(debug=True)
