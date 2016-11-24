import arrow
import json
from flask import jsonify, request
from orlo import app
from orlo.orm import db, Package, Release, PackageResult, ReleaseNote, Platform
from orlo.util import validate_request_json
from orlo.user_auth import token_auth
from sqlalchemy.orm import exc

__author__ = 'alforbes'


@token_auth.token_required
@app.route('/releases/import', methods=['GET'])
def get_import():
    """
    Display a useful message on how to import

    :status 200:
    """

    msg = 'This is the orlo import url'
    return jsonify(message=msg), 200


@app.route('/releases/import', methods=['POST'])
def post_import():
    """
    Import a release.

    This endpoint is designed to created releases in bulk. It bypasses the normal workflow,
    and may be an option for those who wish to "publish" a release after the fact rather than step
    through as it happens.

    The document must contain a list of full releases, in json format. Example:

    .. code-block:: python

        [
            {
                "platforms": [
                  "GumtreeUK"
                ],
                "stime": "2015-12-17T17:02:04Z",
                "ftime": "2015-12-17T17:02:24Z",
                "team": "Gumtree UK Site Operations",
                "references": [
                  "TICKET-1"
                ],
                "notes": [
                  "Imported from other_system"
                ],
                "packages": [
                    {
                        "name": "",
                        "diff_url": null,
                        "stime": "2015-12-17T17:02:22Z"
                        "ftime": 1450371742,
                        "rollback": false,
                        "status": "SUCCESSFUL",
                        "version": "1.0.1",
                    }
                ],
                "user": "user_one"
            },
            {...}
        ]

    Timestamps can be any format understood by Arrow (note mix of unix time and ISO timestamps
    above).

    Status must be one of the enums accepted by `orlo.orm.Package.status`, i.e.:
    NOT_STARTED, IN_PROGRESS, SUCCESSFUL, FAILED

    A json null value is acceptable for non-required fields, or it can be omitted entirely.
    See `orlo.orm.Release` and `orlo.orm.Package`.

    **Example curl**:

    .. sourcecode:: shell

        curl -v -X POST -d @releases.json 'http://127.0.0.1:5000/releases/import' -H \
        "Content-Type: application/json"

    :status 200: The document was accepted
    """

    validate_request_json(request)

    releases = []
    for r in request.json:
        # Get the platform, create if it doesn't exist
        platforms = []
        for p in r['platforms']:
            try:
                query = db.session.query(Platform).filter(Platform.name == p)
                platform = query.one()
            except exc.NoResultFound:
                app.logger.info("Creating platform {}".format(p))
                platform = Platform(p)
                db.session.add(platform)
            platforms.append(platform)

        release = Release(
                platforms=platforms,
                user=r['user'],
                team=r.get('team'),
                references=json.dumps(r.get('references')),
        )

        release.stime = arrow.get(r['stime']) if r.get('stime') else None
        release.ftime = arrow.get(r['ftime']) if r.get('ftime') else None
        if release.ftime and release.stime:
            release.duration = release.ftime - release.stime

        notes = r.get('notes')
        if notes:
            for n in notes:
                note = ReleaseNote(release.id, n)
                db.session.add(note)

        for p in r['packages']:
            package = Package(
                    release_id=release.id,
                    name=p['name'],
                    version=p['version'],
            )

            package.rollback = p.get('rollback')
            package.status = p.get('status')
            package.diff_url = p.get('diff_url')

            if p.get('stime'):
                package.stime = arrow.get(p['stime'])
            else:
                package.stime = arrow.get(r['stime'])
            package.ftime = arrow.get(p['ftime']) if p.get('ftime') else None
            if package.stime and package.ftime:
                package.duration = package.ftime - package.stime

            db.session.add(package)

        db.session.add(release)
        db.session.commit()

        releases.append(release.id)

    return jsonify({'releases': [str(x) for x in releases]}), 200
