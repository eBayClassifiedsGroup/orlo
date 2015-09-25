from __future__ import print_function

__author__ = 'alforbes'
from flask.ext.sqlalchemy import SQLAlchemy
from sponge import app
from datetime import datetime

db = SQLAlchemy(app)


class DbRelease(db.Model):
    """
    The main Release object
    """
    __tablename__ = 'release'

    id = db.Column(db.String, primary_key=True)
    notes = db.Column(db.String)
    platform = db.Column(db.String)
    reference = db.Column(db.String(18))
    stime = db.Column(db.DateTime)
    duration = db.Column(db.Time)
    user_id = db.Column(db.String)
    team_id = db.Column(db.String)

    def __init__(self, id, platform, user, reference="", notes=""):
        self.id = id
        self.notes = notes
        self.platform = platform
        self.reference = reference
        self.user = user

    def start(self):
        """
        Mark a release as started
        """
        self.stime = datetime.now()

    def stop(self):
        """
        Mark a release as stopped
        """
        if not self.duration:
            self.duration = datetime.now() - self.stime


class DbPackage(db.Model):
    """
    A deployed instance of a package
    """
    __tablename__ = 'package'

    id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String(120))
    stime = db.Column(db.DateTime)
    duration = db.Column(db.Time)
    success = db.Column(db.Boolean)
    version = db.Column(db.String(16))

    release_id = db.Column(db.Integer, db.ForeignKey("release.id"))
    release = db.relationship("DbRelease", backref=db.backref('packages',
                                                              order_by=id))

    def __init__(self, id, release_id, name, version):
        self.id = id
        self.name = name
        self.version = version
        self.release_id = release_id

    def start(self):
        """
        Mark a deployment as started
        """
        self.stime = datetime.now()

    def stop(self, success):
        """
        Mark a deployment as stopped
        """
        if not self.ftime:
            self.duration = datetime.now() - self.stime
        self.success = success


class DbResults(db.Model):
    """
    The results of a package.
    """
    __tablename__ = 'results'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    content = db.Column(db.Text)

    package_id = db.Column(db.Integer, db.ForeignKey("package.id"))
    package = db.relationship("DbPackage", backref=db.backref('results',
                                                              order_by=id))

    def __init__(self, package_id, content):
        self.package_id = package_id
        self.content = content
