.. orlo documentation master file, created by
   sphinx-quickstart on Tue Oct 27 17:16:14 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Orlo
======

Orlo is an API for tracking deployments, written with Python, Flask and SqlAlchemy.

It originated as part of a siteops hackathon at eBay classifieds, and is currently in development by staff at gumtree.com, kijiji.ca, mobile.de and 2dehands.be (all part of eBay Classifieds).

It is in a very early stage of development, but eventually we hope that it will be used more broadly within ECG and possibly elsewhere.


Contents
--------

.. toctree::
    :maxdepth: 2

    install
    rest


About Orlo
------------

Orlo aims to cover the needs of all eCG platforms with respect to gathering information about deployments, while being simple to integrate with existing deployment software and scripts. This currently includes:

  - Person who performed the release
  - Dev team responsible
  - Platforms deployed to
  - Start time, finish time, and duration by package
  - Versions of packages released
  - External references such as issue tracking tickets
  - Output such as logs

With this information, it will be possible to build dashboards and more intelligent release tooling.

The API should also be agnostic to release process, server container or packaging format - all platforms do things differently. It should be forgiving and "do the right thing" in the case of missing data, as not all platforms will use every field.

Why "orlo"?
-------------

Originally this project was called "Sponge", because sponges are absorbent. But it turns out that name was already in use on readthedocs.org, so it was renamed. In English, orlo means "a plinth supporting the base of a column", which seems like a pretty good analogy for this project.

Roadmap
-------

In the beginning:
 - Records release information in a database
 - Returns release information in JSON
 - API documentation

In the future:
 - UI to display and consume the data
 - Control API for performing deployments
