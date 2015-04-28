import logging
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


__all__ = ['DockerImage', 'AnonymousImage']


class AnonymousImage(Exception):
    pass

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

    def inspect(self):
        if self.id_:
            name = self.id_
        elif self.tags:
            name = self.tags[0]
        else:
            raise AnonymousImage()
        i = self.client.image_inspect(name, raw=True)
        self.id_ = i['Id'],
        self.created = i['Created']
        self.size = i['Size']
        self.parent = i['Parent']
