from xd.docker.image import Image
from xd.docker.datetime import strptime

import logging
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


__all__ = ['Container']


class ContainerState(object):
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


class Container(object):
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
        'Id', 'Names', 'Command', 'Created', 'Status', 'Ports',
        'Labels', 'SizeRW', 'SizeRootFs')

    def _parse_list_response(self, response):
        image_name = response['Image']
        image_id = response.get('ImageID')
        self.image = Image(self.client, image_id, tags=[image_name])
        for name in self.LIST_RESPONSE_ATTRS:
            try:
                value = response[name]
            except KeyError:
                continue
            if name == 'Names':
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
        self._parse_more_attrs(self.CONFIG_ATTRS,
                               response.get('Config'))
        self._parse_more_attrs(self.HOST_CONFIG_ATTRS,
                               response.get('HostConfig'))
        self._parse_more_attrs(self.NETWORK_SETTINGS_ATTRS,
                               response.get('NetworkSettings'))
        if 'State' in response:
            self.state = ContainerState(response.get('State'))

    def _parse_more_attrs(self, attrs, response):
        for name in attrs:
            try:
                value = response[name]
            except KeyError:
                continue
            setattr(self, name.lower(), value)

    CONFIG_ATTRS = (
        'AttachStderr', 'AttachStdin', 'AttachStdout', 'Cmd', 'Domainname',
        'Entrypoint', 'Env', 'ExposedPorts', 'Hostname', 'Image', 'Labels',
        'MacAddress', 'NetworkDisabled', 'OnBuild', 'OpenStdin', 'StdinOnce',
        'Tty', 'User', 'Volumes', 'WorkingDir')

    HOST_CONFIG_ATTRS = (
        'Binds', 'BlkioWeight', 'CapAdd', 'CapDrop', 'ContainerIDFile',
        'CpusetCpus', 'CpusetMems', 'CpuShares', 'CpuPeriod', 'Devices', 'Dns',
        'DnsSearch', 'ExtraHosts', 'IpcMode', 'Links', 'LxcConf', 'Memory',
        'MemorySwap', 'OomKillDisable', 'NetworkMode', 'PortBindings',
        'Privileged', 'ReadonlyRootfs', 'PublishAllPorts', 'RestartPolicy',
        'LogConfig', 'SecurityOpt', 'VolumesFrom', 'Ulimits')

    NETWORK_SETTINGS_ATTRS = (
        "Bridge", "Gateway", "IPAddress", "IPPrefixLen", "MacAddress",
        "PortMapping", "Ports")
