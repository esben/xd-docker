import logging
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

from xd.docker.image import *


__all__ = ['DockerContainer']


class DockerContainer(object):
    """Docker container."""

    def __init__(self, client, id_=None, names=None, command=None, ports=None,
                 image=None, created=None):
        """Docker container concstructor."""
        self.client = client
        self.id_ = id_
        self.names = names
        self.command = command
        self.ports = ports
        if image is not None:
            self.image = DockerImage(image)
        else:
            self.image = None
        self.created = created
