Introduction
============

XD Docker is a Python library for accessing services providing a Docker Remote
API compatible interface (ie. Docker Engine and Docker Swarm), built on top of
the Requests_ library.

The primary goal of XD Docker is to provide a stable, easy-to-use and Pythonic
API for writing applications that use Docker Remote API.  When this is
achieved, more advanced features might be added on top of it.

.. _Requests: http://python-requests.org

XD Docker is compatible with Python 3.4 and newer, and Docker Remote API
version 1.14 and newer.  Support for older Python versions should be possible
(patches are welcome).  Support for older Docker Remote API versions should
also be possible, but the current integration test cannot supported these due
to Docker HUB not supporting older clients, so official support in XD Docker
is not likely.
