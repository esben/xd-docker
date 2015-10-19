import logging
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

from xd.docker.image import *
from xd.docker.datetime import *


__all__ = ['DockerContainer']


class DockerContainerState(object):
    def __init__(self, state):
        assert state is not None
        self.error = state.get('Error', None)
        self.exit_code = state.get('ExitCode', None)
        self.finished_at = strptime(state.get('FinishedAt', None))
        self.oom_killed = state.get('OOMKilled', None)
        self.paused = state.get('Paused', None)
        self.pid = state.get('Pid', None)
        self.restarting = state.get('Restarting', None)
        self.running = state.get('Running', None)
        self.started_at = strptime(state.get('StartedAt', None))

    @property
    def execution_time(self):
        return (self.finished_at - self.started_at)


class DockerContainer(object):
    """Docker container."""

    def __init__(self, client, id=None, name=None,
                 list_response=None, inspect_response=None):
        """Docker container concstructor."""
        self.client = client
        self.id = id
        self.name = name
        if list_response:
            self._parse_list_response(list_response)
        if inspect_response:
            self._parse_inspect_response(inspect_response)

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

    INSPECT_RESPONSE_ATTRS = (
        'AppArmorProfile', 'Args', 'Created', 'Driver', 'ExecDriver',
        'ExecIDs', 'HostnamePath', 'LogPath', 'Id', 'Image', 'MountLabel',
        'Name', 'Path', 'ProcessLabel', 'ResolveConfPath', 'RestartCount',
        'Mounts')

    def _parse_inspect_response(self, response):
        response = response.copy()
        for name in self.INSPECT_RESPONSE_ATTRS:
            try:
                value = response.pop('Id')
            except KeyError:
                continue
            setattr(self, name.lower(), value)
        self._parse_config(response.get('Config'))
        self._parse_host_config(response.get('HostConfig'))
        self._parse_network_settings(response.get('NetworkSettings'))
        if 'State' in response:
            self.state = DockerContainerState(response.get('State'))


    CONFIG_ATTRS = (
        'AttachStderr', 'AttachStdin', 'AttachStdout', 'Cmd', 'Domainname',
        'Entrypoint', 'Env', 'ExposedPorts', 'Hostname', 'Image', 'Labels',
        'MacAddress', 'NetworkDisabled', 'OnBuild', 'OpenStdin', 'StdinOnce',
        'Tty', 'User', 'Volumes', 'WorkingDir')

    def _parse_config(self, response):
        for name in self.CONFIG_ATTRS:
            try:
                value = response[name]
            except KeyError:
                continue
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

    NETWORK_SETTINGS_ATTRS = (
        "Bridge", "Gateway", "IPAddress", "IPPrefixLen", "MacAddress",
        "PortMapping", "Ports")

    def _parse_network_settings(self, response):
        for name in self.NETWORK_SETTINGS_ATTRS:
            try:
                value = response[name]
            except KeyError:
                continue
            setattr(self, name.lower(), value)
