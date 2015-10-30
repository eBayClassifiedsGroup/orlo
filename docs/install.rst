Installation
============

**This is a rough draft**
    This documentation is in an early state and your mileage may vary, please raise issues on github for any problems you encounter.

Currently, we do not publish packages to pip, thus the only way is currently from source, but this may change when the project reaches maturity.

From source
-----------

Clone the github repo:

::

    git clone https://github.com/eBayClassifiedsGroup/sponge.git
    cd sponge
    python setup.py install


Developing in Vagrant
---------------------

Install Vagrant as per the docs, cd to the git clone of sponge and run `vagrant up`.

From here you should be able to do `cd /vagrant` followed by `python setup.py install`.

Tests can be run with `python setup.py test`.

Building the debian package
---------------------------

This is not as nice as it could be at present but will improve in future. The main problem is that dh-virtualenv as supplied in jessie is too old, so you will need to obtain a version > 0.9. For this I suggest the repo provided by the author: https://launchpad.net/~spotify-jyrki/+archive/ubuntu/dh-virtualenv

Other than that, the vagrant environment is mostly setup to do this, so I suggest starting from there.

The debian packages you will need (already installed by Vagrant) are:

::

    sudo apt-get -y install python-pip python-dev postgresql postgresql-server-dev-all build-essential git-buildpackages debhelper python-dev

(plus dh-virtualenv)

It should work on Ubuntu 14.04 and Debian Jessie onwards.

From there, cd into a copy of the sponge repo and run `make debian`.

If you have made changes beforehand, it is a good idea to update the version in setup.py and run `make changelog` first so that your package is distinct from any that we release. You will need to have git configured for this (git-dch will tell you on invocation).

Initial Configuration
---------------------

The debian package provides a script to perform actions such as writing the config, setting up the database and running a test server. This can be found in the source at `bin/sponge`.

::

    sudo sponge write_config

Database setup
--------------

Sponge uses SQLAlchemy ORM which can use many database backends, but our instances use Postgres. Tests are run against in-memory SQLite, thus for small deploys sqlite should be fine, but you may run into problems with concurrent users. We strongly suggest setting up a proper database such as postgres.

Postgres
````````

::

    sudo -u postgres -i
    psql

From the psql prompt:

::

    postgres=# create user sponge with password 'my-secure-password';
    CREATE ROLE
    postgres=# create database sponge owner sponge;
    CREATE DATABASE
    postgres=#

Update uri under [db] in sponge.conf, e.g.

::

    uri = postgres://sponge:my-secure-password@localhost:5432/sponge


SQLite
``````
Create a directory for the db, e.g. :

::

    mkdir /var/lib/sponge
    chown sponge:root /var/lib/sponge

Update the uri under [db] in sponge.conf to point to a file in this directory:

::

    uri = sqlite:///var/lib/sponge/database.sqlite

Both
````

If installed from the debian package run

::

    sponge setup_database

If you are running from source the sponge script can be found in ./bin, but you may need to invoke it explicity from your python interpreter, as it is hard-coded to the dh-virtualenv path.


Running under Gunicorn
----------------------
Under ./etc an example systemd unit file is provided, but to run it in the foreground with 4 workers do:

::

    gunicorn -w 4 -b 127.0.0.1:8080 sponge:app

Test it is running:

::

    curl -v 127.0.0.1:8080/ping

And it should return 'pong'


Nginx Setup
-----------
We strongly recommend running sponge behind a proxy such as nginx. An example configuration is provided under ./etc/
