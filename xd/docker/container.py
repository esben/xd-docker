import logging
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

from xd.docker.image import *


__all__ = ['DockerContainer']


class DockerContainer(object):
    """Docker container."""

    def __init__(self, client, id=None, name=None,
                 list_response=None):
        """Docker container concstructor."""
        self.client = client
        self.id = id
        self.name = name
        if list_response:
            self._parse_list_response(list_response)

    LIST_RESPONSE_ATTRS = (
        'Id', 'Names', 'Image', 'Command', 'Created', 'Status', 'Ports',
        'Labels', 'SizeRW', 'SizeRootFs')

    def _parse_list_response(self, response):
        for name in self.LIST_RESPONSE_ATTRS:
            try:
                value = response[name]
            except KeyError:
                continue
            if name == 'Image':
                value = DockerImage(self.client, tags=[value])
            elif name == 'Names':
                assert isinstance(value, list)
                assert len(value) == 1
                (value,) = value
            setattr(self, name.lower(), value)

    HOST_CONFIG_ATTRS = (
        'Binds', 'BlkioWeight', 'CapAdd', 'CapDrop', 'ContainerIDFile',
        'CpusetCpus', 'CpusetMems', 'CpuShares', 'CpuPeriod', 'Devices', 'Dns',
        'DnsSearch', 'ExtraHosts', 'IpcMode', 'Links', 'LxcConf', 'Memory',
        'MemorySwap', 'OomKillDisable', 'NetworkMode', 'PortBindings',
        'Privileged', 'ReadonlyRootfs', 'PublishAllPorts', 'RestartPolicy',
        'LogConfig', 'SecurityOpt', 'VolumesFrom', 'Ulimits')

    def _parse_host_config(self, response):
        for name in self.HOST_CONFIG_ATTRS:
            try:
                value = response[name]
            except KeyError:
                continue
            setattr(self, name.lower(), value)
