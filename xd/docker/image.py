import logging
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


__all__ = ['DockerImage']


class DockerImage(object):
    """Docker image."""

    def __init__(self, client, id_=None, created=None, tags=None,
                 size=None, virtual_size=None, parent=None,
                 context=None, dockerfile=None):
        """Docker image concstructor."""
        self.client = client
        self.id_ = id_
        self.created = created
        self.tags = tags
        self.size = size
        self.virtual_size = virtual_size
        self.parent = parent
        self.context = context
        self.dockerfile = dockerfile
