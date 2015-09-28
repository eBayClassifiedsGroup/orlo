# Sponge
[![Build Status](https://travis-ci.org/eBayClassifiedsGroup/sponge.svg?branch=master)](https://travis-ci.org/eBayClassifiedsGroup/sponge/)

An API for tracking deployments, written with Python, Flask and SqlAlchemy.

## Introduction

Sponge originated as part of a siteops hackathon at eBay classifieds, and is currently in development by staff at gumtree.com, kijiji.ca, mobile.de and 2dehands.be (all part of eBay Classifieds).

It is in a very early stage of development, but eventually we hope that it will be used more broadly within ECG and possibly elsewhere.

The goal is to build an API specification in Python, which covers the needs of all platforms with respect to gathering information about deployments, while being simple to integrate with existing deployment software and scripts.
This might include, but is not limited to:
- Release information and metrics, such as:
  - Person who performed the release
  - Dev team responsible
  - Overall release duration
  - Package release duration
  - Versions of packages released
  - Hosts deployed to
  - Logs
  - Ticket / external reference of some kind
- Returning release information for use in UIs and other tools
  - Current deployed version of a package
  - Information on past releases
  - Information on any ongoing releases
  - Hosts involved in a release

The API should also be agnostic to release process, server container or packaging format - all platforms do things differently. It should be forgiving and "do the right thing" in the case of missing data, as not all platforms will use every field.

## Why Sponge?

Sponges are very absorbant. Sponge absorbs data. Also, it provides a good set of analogies by way of a popular children's TV show...

# Road map

In the begining:
 - Records release information in a database
 - Returns release information in JSON
 - API documentation

In future:
 - UI to display and consume the data
 - Control API for performing deployments

## Endpoints

`/release`

Method: POST
Example:
```
curl -i -H "Content-Type: application/json" -X POST -d \
'{
   "notes":    "My first milestone",
   "references":     ["ACBC-1234"],
   "platforms":     ["My_Platform"]
 }' \
 http://localhost:5000/release
```


`/relase/{id}/packages`

Method: POST
Example:


`/results`

Method: POST
Example:
