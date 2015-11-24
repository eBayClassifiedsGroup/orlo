#!/usr/bin/env python
from orlo import app

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///orlo.db'

app.run(host='0.0.0.0', port=5000, debug=True)
