# Orlo
[![Build Status](https://travis-ci.org/eBayClassifiedsGroup/orlo.svg?branch=master)](https://travis-ci.org/eBayClassifiedsGroup/orlo/) [![Documentation Status](https://readthedocs.org/projects/orlo/badge/?version=latest)](http://orlo.readthedocs.org/en/latest/?badge=latest)


An API for tracking deployments, written with Python, Flask and SqlAlchemy.

## About

Orlo originated as part of a siteops hackathon at eBay classifieds, and is currently in development by staff at gumtree.com, kijiji.ca, mobile.de and 2dehands.be (all part of eBay Classifieds).
It aims to cover the needs of all eCG platforms with respect to gathering information about deployments, while being simple to integrate with existing deployment software and scripts. This currently includes:

  - Person who performed the release
  - Dev team responsible
  - Platforms deployed to
  - Start time, finish time, and duration by package
  - Versions of packages released
  - External references such as issue tracking tickets
  - Output such as logs

With this information, it will be possible to build dashboards and more intelligent release tooling.

The API should also be agnostic to release process, server container or packaging format - all platforms do things differently. It should be forgiving and "do the right thing" in the case of missing data, as not all platforms will use every field.

# Road map

In the begining:
 - Records release information in a database
 - Returns release information in JSON
 - API documentation

In future:
 - UI to display and consume the data
 - Control API for performing deployments

## Documentation

[http://orlo.readthedocs.org](http://orlo.readthedocs.org)

For sources, see the docs/ directory. Documentation can be compiled with `make html`.
