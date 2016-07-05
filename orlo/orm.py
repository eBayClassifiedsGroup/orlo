from flask_sqlalchemy import SQLAlchemy
from sqlalchemy_utils.types.uuid import UUIDType
from sqlalchemy_utils.types.arrow import ArrowType

from orlo import app, config
from orlo.exceptions import OrloWorkflowError
import pytz
import uuid
import arrow
import json

__author__ = 'alforbes'

db = SQLAlchemy(app)

try:
    TIMEZONE = pytz.timezone(config.get('main', 'time_zone'))
except pytz.exceptions.UnknownTimeZoneError:
    app.logger.critical(
        'Unknown time zone "{}", see pytz docs for valid values'.format(
            config.get('main', 'timezone')
        ))


# Map releases to platforms
release_platform = db.Table(
    'release_platform', db.Model.metadata,
    db.Column('release_id', UUIDType, db.ForeignKey('release.id')),
    db.Column('platform_id', UUIDType, db.ForeignKey('platform.id'))
)


def string_to_list(string):
    """
    Load a list from a string

    :param string:
    :return:
    """
    if string is None:
        return []

    if '[' in string and ']' in string and ('"' in string or "'" in string):
        # Valid list syntax, presumably...
        # TODO a regex would be better here
        return json.loads(string.replace("'", '"'))
    else:
        # assume just one item
        return [string]


class Release(db.Model):
    """
    The main Release object
    """
    __tablename__ = 'release'

    id = db.Column(UUIDType, primary_key=True, unique=True, nullable=False)
    platforms = db.relationship('Platform', secondary=release_platform)
    references = db.Column(db.String)
    stime = db.Column(ArrowType, index=True)
    ftime = db.Column(ArrowType)
    duration = db.Column(db.Interval)
    user = db.Column(db.String, nullable=False)
    team = db.Column(db.String)
    packages = db.relationship("Package", backref=db.backref("release"))

    def __init__(self, platforms, user, team=None, references=None):
        # platforms and references are stored as strings in DB but really are lists
        self.id = uuid.uuid4()
        self.platforms = platforms
        self.user = user

        if team:
            self.team = team
        if references:
            self.references = str(references)

        # Assume the release started when it was created
        self.start()

    def __str__(self):
        return self.to_dict()

    def to_dict(self):
        time_format = config.get('main', 'time_format')

        metadata = {}
        for m in self.metadata:
            metadata.update(m.to_dict())

        return {
            'id': str(self.id),
            'packages': [p.to_dict() for p in self.packages],
            'platforms': [platform.name for platform in self.platforms],
            'references': string_to_list(self.references),
            'stime': self.stime.strftime(config.get('main', 'time_format')) if self.stime else None,
            'ftime': self.ftime.strftime(config.get('main', 'time_format')) if self.ftime else None,
            'duration': self.duration.seconds if self.duration else None,
            'metadata': metadata,
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


class Package(db.Model):
    """
    A deployed instance of a package
    """
    __tablename__ = 'package'

    id = db.Column(UUIDType, primary_key=True, unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    stime = db.Column(ArrowType, index=True)
    ftime = db.Column(ArrowType)
    duration = db.Column(db.Interval)
    status = db.Column(
        db.Enum('NOT_STARTED', 'IN_PROGRESS', 'SUCCESSFUL', 'FAILED',
                name='status_types'),
        default='NOT_STARTED')
    version = db.Column(db.String(32), nullable=False)
    diff_url = db.Column(db.String)
    rollback = db.Column(db.Boolean(create_constraint=True))
    release_id = db.Column(UUIDType, db.ForeignKey("release.id"))

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

        :param success: Whether or not the package deploy succeeded
        """
        if self.stime is None:
            raise OrloWorkflowError(
                "Can not stop a package which has not been started")
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
            'id': str(self.id),
            'name': self.name,
            'version': self.version,
            'stime': self.stime.strftime(config.get('main', 'time_format')) if self.stime else None,
            'ftime': self.ftime.strftime(config.get('main', 'time_format')) if self.ftime else None,
            'duration': self.duration.seconds if self.duration else None,
            'rollback': self.rollback,
            'status': self.status,
            'diff_url': self.diff_url,
        }


class PackageResult(db.Model):
    """
    The results of a package
    """
    __tablename__ = 'package_result'

    id = db.Column(UUIDType, primary_key=True, unique=True)
    content = db.Column(db.Text)

    package_id = db.Column(UUIDType, db.ForeignKey("package.id"))
    package = db.relationship("Package", backref=db.backref('results',
                                                            order_by=id))

    def __init__(self, package_id, content):
        self.id = uuid.uuid4()
        self.package_id = package_id
        self.content = content


class ReleaseNote(db.Model):
    """
    Notes added to a release
    """
    __tablename__ = 'release_note'

    id = db.Column(UUIDType, primary_key=True, unique=True)
    content = db.Column(db.Text, nullable=False)

    release_id = db.Column(UUIDType, db.ForeignKey("release.id"))
    release = db.relationship("Release", backref=db.backref('notes', order_by=id))

    def __init__(self, release_id, content):
        self.id = uuid.uuid4()
        self.release_id = release_id
        self.content = content


class ReleaseMetadata(db.Model):
    """
    Metadata added to a release
    """
    __tablename__ = 'release_metadata'

    id = db.Column(UUIDType, primary_key=True, unique=True)

    release_id = db.Column(UUIDType, db.ForeignKey("release.id"))
    release = db.relationship("Release", backref=db.backref('metadata', order_by=id))
    key = db.Column(db.Text, nullable=False)
    value = db.Column(db.Text, nullable=False)

    def __init__(self, release_id, key, value):
        self.id = uuid.uuid4()
        self.release_id = release_id
        self.key = key
        self.value = value

    def getKey(self):
        return str(self.key)

    def to_dict(self):
        return {self.key: self.value}


class Platform(db.Model):
    """
    A platform that is released to
    """
    __tablename__ = 'platform'

    id = db.Column(UUIDType, primary_key=True, unique=True)
    name = db.Column(db.Text, nullable=False, unique=True)

    def __init__(self, name):
        self.id = uuid.uuid4()
        self.name = name
