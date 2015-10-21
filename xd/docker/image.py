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
        self.id = id_
        self.created = created
        self.tags = tags
        self.size = size
        self.virtual_size = virtual_size
        self.parent = parent
        self.context = context
        self.dockerfile = dockerfile

    def inspect(self):
        if self.id:
            name = self.id
        elif self.tags:
            name = self.tags[0]
        else:
            raise AnonymousImage()
        i = self.client.image_inspect(name, raw=True)
        self.id = i['Id'],
        self.created = i['Created']
        self.size = i['Size']
        self.parent = i['Parent']

    def build(self, **kwargs):
        if 'name' in kwargs:
            self.tags = [kwargs['name']]
        else:
            self.tags = []
        self.id = self.client.image_build(
            self.context, dockerfile=self.dockerfile, **kwargs)
        self.created = None
        self.virtual_size = None
        self.parent = None
        self.size = None
