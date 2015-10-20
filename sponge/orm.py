from __future__ import print_function

__author__ = 'alforbes'
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy_utils.types.uuid import UUIDType

from sponge import app, config
from datetime import datetime, timedelta
import pytz
import uuid

db = SQLAlchemy(app)

try:
   TIMEZONE = pytz.timezone(config.get('main', 'time_zone'))
except pytz.exceptions.UnknownTimeZoneError:
    app.logger.critical(
        'Unknown time zone "{}", see pytz docs for valid values'.format(
            config.get('main', 'timezone')
        ))


class DbRelease(db.Model):
    """
    The main Release object
    """
    __tablename__ = 'release'

    id = db.Column(UUIDType, primary_key=True, unique=True, nullable=False)
    notes = db.Column(db.String)
    platforms = db.Column(db.String, nullable=False)
    references = db.Column(db.String)
    stime = db.Column(db.DateTime)
    ftime = db.Column(db.DateTime)
    duration = db.Column(db.Interval)
    user = db.Column(db.String, nullable=False)
    team = db.Column(db.String)
    timezone = db.Column(db.String, default=config.get('main', 'time_zone'),
                         nullable=False)

    def __init__(self, platforms, user,
                 notes=None, team=None, references=None):
        self.id = uuid.uuid4()
        self.platforms = str(platforms)
        self.user = user

        if notes:
            self.notes = str(notes)
        if team:
            self.team = team
        if references:
            self.references = str(references)

        # Assume the release started when it was created
        self.start()

    def __str__(self):
        return unicode(self.to_dict())

    def to_dict(self):
        time_format = config.get('main', 'time_format')
        return {
            'id': unicode(self.id),
            'platforms': self.platforms,
            'references': self.references,
            'stime': self.stime.strftime(time_format) if self.stime else None,
            'ftime': self.ftime.strftime(time_format) if self.ftime else None,
            'duration': self.duration.seconds if self.duration else None,
            'user': self.user,
            'team': self.team,
            'timezone': self.timezone,
        }

    def start(self):
        """
        Mark a release as started
        """
        self.stime = datetime.utcnow()

    def stop(self):
        """
        Mark a release as stopped
        """
        self.ftime = datetime.utcnow()
        td = self.ftime - self.stime
        self.duration = td


class DbPackage(db.Model):
    """
    A deployed instance of a package
    """
    __tablename__ = 'package'

    id = db.Column(UUIDType, primary_key=True, unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    stime = db.Column(db.DateTime)
    ftime = db.Column(db.DateTime)
    duration = db.Column(db.Interval)
    status = db.Column(
        db.Enum('NOT_STARTED', 'IN_PROGRESS', 'SUCCESSFUL', 'FAILED'),
        default='NOT_STARTED')
    version = db.Column(db.String(16), nullable=False)
    diff_url = db.Column(db.String)
    timezone = db.Column(db.String, default=config.get('main', 'time_zone'),
                         nullable=False)

    release_id = db.Column(UUIDType, db.ForeignKey("release.id"))
    release = db.relationship("DbRelease", backref=db.backref('packages',
                                                              order_by=stime))

    def __init__(self, release_id, name, version):
        self.id = uuid.uuid4()
        self.name = name
        self.version = version
        self.release_id = release_id

    def start(self):
        """
        Mark a package deployment as started
        """
        self.stime = datetime.utcnow()
        self.status = 'IN_PROGRESS'

    def stop(self, success):
        """
        Mark a package deployment as stopped
        """
        self.ftime = datetime.utcnow()
        td = self.ftime - self.stime
        self.duration = td

        if success:
            self.status = 'SUCCESSFUL'
        else:
            self.status = 'FAILED'


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
