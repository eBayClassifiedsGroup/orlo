from __future__ import print_function, unicode_literals

from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy_utils.types.uuid import UUIDType
from sqlalchemy_utils.types.arrow import ArrowType

from orlo import app, config
from orlo.util import string_to_list
from datetime import datetime, timedelta
import pytz
import uuid
import arrow

__author__ = 'alforbes'

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
    stime = db.Column(ArrowType)
    ftime = db.Column(ArrowType)
    duration = db.Column(db.Interval)
    user = db.Column(db.String, nullable=False)
    team = db.Column(db.String)

    def __init__(self, platforms, user,
                 notes=None, team=None, references=None):
        # platforms and references are stored as strings in DB but really are lists
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
            'packages': [p.to_dict() for p in self.packages],
            'platforms': string_to_list(self.platforms),
            'references': string_to_list(self.references),
            'stime': self.stime.strftime(config.get('main', 'time_format')) if self.stime else None,
            'ftime': self.ftime.strftime(config.get('main', 'time_format')) if self.ftime else None,
            'duration': self.duration.seconds if self.duration else None,
            'user': self.user,
            'team': self.team,
        }

    def start(self):
        """
        Mark a release as started
        """
        self.stime = arrow.now(config.get('main', 'time_zone'))

    def stop(self):
        """
        Mark a release as stopped
        """
        self.ftime = arrow.now(config.get('main', 'time_zone'))
        td = self.ftime - self.stime
        self.duration = td


class DbPackage(db.Model):
    """
    A deployed instance of a package
    """
    __tablename__ = 'package'

    id = db.Column(UUIDType, primary_key=True, unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    stime = db.Column(ArrowType)
    ftime = db.Column(ArrowType)
    duration = db.Column(db.Interval)
    status = db.Column(
        db.Enum('NOT_STARTED', 'IN_PROGRESS', 'SUCCESSFUL', 'FAILED',
                name='status_types'),
        default='NOT_STARTED')
    version = db.Column(db.String(16), nullable=False)
    diff_url = db.Column(db.String)
    rollback = db.Column(db.Boolean(create_constraint=True))
    release_id = db.Column(UUIDType, db.ForeignKey("release.id"))
    release = db.relationship("DbRelease", backref=db.backref('packages',
                                                              order_by=stime))

    def __init__(self, release_id, name, version, diff_url=None, rollback=False):
        self.id = uuid.uuid4()
        self.name = name
        self.version = version
        self.release_id = release_id
        self.diff_url = diff_url
        self.rollback = rollback

    def start(self):
        """
        Mark a package deployment as started
        """
        self.stime = arrow.now(config.get('main', 'time_zone'))
        self.status = 'IN_PROGRESS'

    def stop(self, success):
        """
        Mark a package deployment as stopped
        """
        self.ftime = arrow.now(config.get('main', 'time_zone'))
        td = self.ftime - self.stime
        self.duration = td

        if success:
            self.status = 'SUCCESSFUL'
        else:
            self.status = 'FAILED'

    def to_dict(self):
        time_format = config.get('main', 'time_format')
        return {
            'id': self.id,
            'name': self.name,
            'version': self.version,
            'stime': self.stime.strftime(config.get('main', 'time_format')) if self.stime else None,
            'ftime': self.ftime.strftime(config.get('main', 'time_format')) if self.ftime else None,
            'duration': self.duration.seconds if self.duration else None,
            'status': self.status,
            'diff_url': self.diff_url,
        }


class DbResults(db.Model):
    """
    The results of a package.
    """
    __tablename__ = 'results'

    id = db.Column(UUIDType, primary_key=True, unique=True)
    content = db.Column(db.Text)

    package_id = db.Column(UUIDType, db.ForeignKey("package.id"))
    package = db.relationship("DbPackage", backref=db.backref('results',
                                                              order_by=id))

    def __init__(self, package_id, content):
        self.id = uuid.uuid4()
        self.package_id = package_id
        self.content = content
