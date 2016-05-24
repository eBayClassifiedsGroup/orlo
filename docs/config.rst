Configuration
=============

[main]
``````

:debug_mode: `true` or `false`. Default `false`. Enables Flask's debug mode.
:propagate_exceptions: `true` or `false`. Default `true`. Sets
    'PROPAGATE_EXCEPTIONS` in Flask. See
    `Flask documentation <http://flask.pocoo.org/docs/0.10/config/#builtin-configuration-values>`_
    for details.
:time_format: A `strftime <https://docs.python.org/2/library/time.html#time.strftime>`_
    string. Default `%Y-%m-%dT%H:%M:%SZ`.
:time_zone: Local time zone, as understood by pytz. Internally,
    all timestamps are stored in UTC. The timestamp is interpreted by Arrow when
    timestamps are given by the user (e.g. on recording a release), this
    setting merely reflects what time zone is given back to GET requests.
    Default `UTC`.
:strict_slashes: `true` or `false`. Default `false`. By default, Werkzeug
    (what Flask uses underneath), will automatically "handle" trailing slashes,
    with the result that /foo/ and /foo are the same url. This disables that
    behaviour. It is recommended that you leave this set to false. See the
    `Werkzeug documentation <http://werkzeug.pocoo.org/docs/0.11/routing/#maps-rules-and-adapters>`_
    for more information.
:base_url: The external url which points to your web app. Required for
    callbacks. Default `http://localhost:8080`.

[security]
``````````

:enabled: `true` or `false`. Enables security.
:passwd_file: Path to a `htpasswd <https://httpd.apache.org/docs/2.2/programs/htpasswd.html>`_
    file to use for authentication.
:secret_key: A secret key to use for token encryption. Default `change_me`.
    If security is enabled and this is still set to `change_me`, Orlo will
    refuse to start.
:token_ttl: The length of times that tokens should live for in seconds.
    Tokens automatically expire after this. Default `3600`.
:ldap_server: Ldap server to use for ldap requests. Default `localhost
    .localdomain`
:ldap_port: Ldap port to use for ldap requests. Default `389`.
:user_base_dn: Ldap dn in which to search for users. Default `ou=people,
    ou=example,ou=test`


[db]
````

:uri: Database uri for SQLAlchemy. See `Flask-SQLAlchemy <http://flask-sqlalchemy.pocoo.org/2.1/config/?highlight=sqlalchemy_database_uri>`_
    docs for details. Default `postgres://orlo:password@localhost:5432/orlo`
:echo_queries: Whether or not to echo sql queries to log. Default `false`.

[logging]
`````````

:level: Logging level, valid values `debug`, `info`, `warning`, `error`.
    Default `info`.
:file: Log file to use. If not set, logging only goes to stdout.

[deploy]
````````

:timeout: How long to wait for the deploy script to complete in seconds. If it
    does not complete within this time, the deploy is considered failed and
    an exception is raised. Default `3600`.

[deploy_shell]
``````````````

:command_path: Path to the deployment script. Defaults to Orlo's test deployer.
