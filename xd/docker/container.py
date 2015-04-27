import logging
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


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
        self.image = image
        self.created = created
