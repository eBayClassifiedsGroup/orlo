#!/usr/bin/env python
from sponge import app

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sponge.db'

app.run(debug=True)
