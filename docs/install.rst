Installation
============

The latest release can be installed using the following command:

.. code-block:: bash

   pip install xd-docker


Dependencies
------------

The following libraries will be automatically installed from PyPI together
with XD Docker:

* requests
* requests-unixsocket
* typing

Docker service
--------------

In order to use XD Docker, you need to have access to a service providing
Docker Remote API, either a Docker Engine or Docker Swarm service.  It needs
to be accessible either through a Unix or TCP socket.
