import re

from xd.docker.parameters import RepoTags, ContainerConfig

import logging
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

__all__ = ['Image', 'AnonymousImage']


class AnonymousImage(Exception):
    pass


class Image(object):
    """Docker image."""

    def __init__(self, client, id=None, tags=None,
                 parent=None, context=None, dockerfile=None,
                 list_response=None, inspect_response=None):
        """Docker image concstructor."""
        self.client = client
        self.id = id
        self.tags = tags
        self.parent = parent
        self.context = context
        self.dockerfile = dockerfile
        if list_response:
            self._parse_response(self.LIST_RESPONSE, list_response)
        if inspect_response:
            self._parse_response(self.INSPECT_RESPONSE, inspect_response)

    def _parse_response(self, fields, response):
        for json_name in fields:
            try:
                value = response[json_name]
            except KeyError:
                continue
            try:
                attr_name = fields[json_name]['attr']
            except:
                attr_name = re.sub(r'([a-z])([A-Z])', r'\1_\2',
                                   json_name).lower()
            parser = self.RESPONSE_PARSER.get(json_name)
            if parser:
                value = parser(value)
            setattr(self, attr_name, value)

    RESPONSE_PARSER = {
        'RepoTags': RepoTags,
        'ContainerConfig': ContainerConfig,
        'Config': ContainerConfig,
    }

    LIST_RESPONSE = (
        'Id', 'RepoTags', 'Created', 'Size', 'VirtualSize', 'Labels')

    INSPECT_RESPONSE = (
        'Id', 'Container', 'Comment', 'Os', 'Architecture', 'Parent',
        'ContainerConfig', 'Config', 'DockerVersion', 'Size', 'VirtualSize',
        'Author', 'Created', 'RepoTags', 'RepoDigests')

    def inspect(self) -> None:
        """Retrieve low-level information for the image."""
        if self.id:
            name = self.id
        elif self.tags:
            name = self.tags[0]
        else:
            raise AnonymousImage()
        response = self.client.image_inspect_raw(name)
        self._parse_response(self.INSPECT_RESPONSE, response)
