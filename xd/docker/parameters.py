"""Module containing helper classes and functions for handling Docker Remote
API parameters."""

import logging
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


import collections
import re
from typing import Any, Optional, Union, Mapping, Sequence, Tuple
from ipaddress import IPv4Address, IPv6Address


__all__ = ['IPAddress', 'Command', 'Signal',
           'Parameter',
           'Env', 'Port', 'PortBinding', 'VolumeMount', 'VolumeBinding',
           'ContainerLink', 'Cpuset', 'HostnameIPMapping', 'VolumesFrom',
           'DeviceToAdd', 'Ulimit', 'LogConfiguration',
           'ContainerConfig', 'HostConfig']


IPAddress = Union[IPv4Address, IPv6Address]
Command = Union[str, Sequence[str]]
Signal = Union[int, str]


class Parameter(object):

    def __str__(self):
        return str(self.json_object())

    def set_str(self, name: str, value: Any):
        if value is not None and not isinstance(value, str):
            value = str(value)
        setattr(self, name, value)

    def set_int(self, name: str, value: Optional[int]):
        if not type(value) in [None, int]:
            value = int(value)
        setattr(self, name, value)

    def set_bool(self, name: str, value: Any):
        if value is not None and not isinstance(value, bool):
            value = bool(value)
        setattr(self, name, value)

    def set_int_or_str(self, name: str, value: Union[int, str]):
        if value is not None and not isinstance(value, int):
            value = str(value)
        setattr(self, name, value)

    def set_list_str(self, name: str, value: Optional[Sequence[str]]):
        if value is not None:
            value = [str(v) for v in value]
        setattr(self, name, value)

    #def set_list_port(self, name: str, value: Optional[Sequence[Port]]):
    def set_list_port(self, name: str, value):
        setattr(self, name, value)

    def set_dict_str_str(self, name: str, value: Optional[Mapping[str, str]]):
        if value is not None:
            value = {k: str(v) for k, v in value.items()}
        setattr(self, name, value)

    def set_list_dict_str_str(self, name: str, value: Optional[Mapping[str, str]]):
        if value is not None:
            value = [{k: str(v) for k, v in i.items()} for i in value]
        setattr(self, name, value)

    def set_command(self, name: str, value: Optional[Command]):
        if isinstance(value, collections.Sequence):
            value = [str(v) for v in value]
        elif value is not None and not isinstance(value, str):
            value = str(value)
        setattr(self, name, value)


class Env(Parameter):
    """Container environment."""

    def __init__(self, env: Optional[Mapping[str, str]]):
        self.env = env

    def json_object(self, api_version):
        if self.env is None:
            return None
        else:
            return ['%s=%s' % (k, v) for k, v in self.env.items()]


class Port(Parameter):
    """Network port."""

    def __init__(self, port: int, protocol: str = 'tcp'):
        if port <= 0 or port > 65535:
            raise ValueError('port must be > 0 and <= 65535')
        self.port = port
        if protocol not in ('tcp', 'udp'):
            raise ValueError("protocol must be either 'tcp' or 'udp'")
        self.protocol = protocol

    def json_object(self, api_version):
        return '%d/%s' % (self.port, self.protocol)


class PortBinding(Parameter):
    """Docker container port binding."""

    def __init__(self, port: int, protocol: str = 'tcp',
                 host_ip: Optional[IPAddress] = None,
                 host_port: Optional[int] = None):
        if port <= 0 or port > 65535:
            raise ValueError('port must be > 0 and <= 65535')
        self.port = port
        if protocol not in ('tcp', 'udp'):
            raise ValueError("protocol must be either 'tcp' or 'udp'")
        self.protocol = protocol
        self.host_ip = host_ip
        if host_port is None:
            host_port = port
        elif host_port <= 0 or host_port > 65535:
            raise ValueError('host_port must be > 0 and <= 65535')
        self.host_port = host_port

    def json_object(self, api_version):
        host_binding = {'HostPort': str(self.host_port)}
        if self.host_ip is not None:
            host_binding['HostIp'] = str(self.host_ip)
        return {'%d/%s' % (self.port, self.protocol): [host_binding]}


class VolumeMount(Parameter):

    def __init__(self, source: str, destination: str, ro: bool = False,
                 label_mode: Optional[str] = None):
        self.source = source
        self.destination = destination
        self.ro = ro
        self.label_mode = label_mode

    def json_object(self, api_version):
        mode = 'ro' if self.ro else 'rw'
        if self.label_mode:
            mode += ',' + self.label_mode
        return {'Source': self.source,
                'Destination': self.destination,
                'RW': not self.ro,
                'Mode': mode}


class VolumeBinding(Parameter):
    """Docker container volume binding."""

    def __init__(self, container_path: str, host_path: Optional[str] = None,
                 ro: bool = False):
        if container_path == '':
            raise ValueError('invalid container_path')
        self.container_path = container_path
        if host_path is None:
            self.host_path = None
        else:
            self.host_path = host_path
        self.ro = ro

    def json_object(self, api_version):
        if not host_path:
            return self.container_path
        if self.ro:
            return '%s:%s:ro' % (self.host_path, self.container_path)
        else:
            return '%s:%s' % (self.host_path, self.container_path)


class ContainerLink(Parameter):
    """Docker container link."""

    def __init__(self, name: str, alias: str):
        self.name = name
        self.alias = alias

    def json_object(self, api_version):
        return '%s:%s' % (self.name, self.alias)


class Cpuset(Parameter):
    """List of CPUs or memory nodes."""

    CPUSET_LIST_RE = re.compile(r'(\d|[1-9]\d+)([,-](\d|[1-9]\d+))*$')

    def __init__(self, cpuset: str):
        if not cpuset:
            self.cpuset = None
        elif not self.CPUSET_LIST_RE.match(cpuset):
            raise ValueError('invalid cpuset: %s' % cpuset)
        else:
            self.cpuset = cpuset

    def json_object(self, api_version):
        return self.cpuset


class HostnameIPMapping(Parameter):
    """Hostname to IP address mapping."""

    def __init__(self, hostname: str, ip: IPAddress):
        self.hostname = hostname
        self.ip = ip

    def json_object(self, api_version):
        return '%s:%s' % (self.hostname, self.ip)


class VolumesFrom(Parameter):
    """Docker container to inherit volumes from."""

    def __init__(self, name: str, ro: bool = False):
        self.name = name
        self.ro = ro

    def json_object(self, api_version):
        return '%s:%s' % (self.name, 'ro' if self.ro else 'rw')


class DeviceToAdd(Parameter):
    """Device to add to docker container."""

    def __init__(self, path_on_host: str,
                 path_in_container: Optional[str] = None,
                 cgroup_permissions: str = 'mrw'):
        self.path_on_host = path_on_host
        if path_in_container is None:
            path_in_container = path_on_host
        self.path_in_container = path_in_container
        self.cgroup_permissions = cgroup_permissions

    def json_object(self, api_version):
        return {'PathOnOhost': self.path_on_host,
                'PathInContainer': self.path_in_container,
                'CgroupPermissions': self.cgroup_permissions}


class Ulimit(Parameter):
    """Ulimit setting."""

    def __init__(self, name: str, soft: int, hard: Optional[int] = None):
        self.name = name
        self.soft = soft
        if hard is None:
            hard = soft
        self.hard = hard

    def json_object(self, api_version):
        return {'Name': self.name,
                'Soft': self.soft,
                'Hard': self.hard}


class LogConfiguration(Parameter):
    """Docker container log configuration."""

    AVAILABLE_TYPES = (
        'json-file', 'syslog', 'journald', 'gelf', 'awslogs', 'none')

    def __init__(self, type: str, config: Mapping[str, str]):
        if type not in self.AVAILABLE_TYPES:
            raise ValueError("invalid type: " + type)
        self.type = type
        self.config = dict(config)

    def json_object(self, api_version):
        return {'Type': self.type, 'Config': self.config}


class ContainerConfig(Parameter):
    """Docker container configuration.

    Arguments:
    image -- image create container from
    command -- command to run (string or list of strings)
    entrypoint -- container entrypoint (string or list of strings)
    on_build -- trigger instructions to be executed later (list of strings)
    hostname -- hostname to use for the container
    domainname -- domain name to use for the container
    user -- user inside the container (user name)
    attach_stdin -- attach to stdin (boolean)
    attach_stdout -- attach to stdout (boolean)
    attach_stderr -- attach to stderr (boolean)
    tty -- attach standard streams to a tty (boolean)
    open_stdin -- open stdin (boolean)
    stdin_once -- close stdin after the client disconnects (boolean)
    env -- environment variables (dict)
    labels -- labels to set on container (dict)
    working_dir -- working directory for command to run in (string)
    mac_address -- MAC address (string)
    network -- whether to enable networking in the container (boolean)
    exposed_ports -- exposed ports (list of ports)
    volumes -- FIXME
    stop_signal -- signal to stop container (int or string)
    """

    # TODO: Figure out how to handle Mounts and Volumes parameters.  It seems
    # like Volumes parameter were replaced by Mounts in 1.20, and the Mounts
    # parameter has more features.  So maybe we should support mounts
    # argument, and then generate Volumes for older API.

    def __init__(self,
                 image: str,
                 command: Optional[Command] = None,
                 entrypoint: Optional[Command] = None,
                 on_build: Optional[Sequence[str]] = None,
                 hostname: Optional[str] = None,
                 domainname: Optional[str] = None,
                 user: Optional[str] = None,
                 attach_stdin: Optional[bool] = None,
                 attach_stdout: Optional[bool] = None,
                 attach_stderr: Optional[bool] = None,
                 tty: Optional[bool] = None,
                 open_stdin: Optional[bool] = None,
                 stdin_once: Optional[bool] = None,
                 env: Mapping[str, str] = None,
                 labels: Optional[Mapping[str, str]] = None,
                 working_dir: Optional[str] = None,
                 network: Optional[bool] = None,
                 mac_address: Optional[str] = None,
                 exposed_ports: Optional[Sequence[Port]] = None,
                 volumes: Optional[Sequence[Mapping[str, str]]] = None,
                 stop_signal: Optional[Union[int, str]] = None):
        self.set_str('image', image)
        self.set_command('command', command)
        self.set_command('entrypoint', entrypoint)
        self.set_list_str('on_build', on_build)
        self.set_str('hostname', hostname)
        self.set_str('domainname', domainname)
        self.set_str('user', user)
        self.set_bool('attach_stdin', attach_stdin)
        self.set_bool('attach_stdout', attach_stdout)
        self.set_bool('attach_stderr', attach_stderr)
        self.set_bool('tty', tty)
        self.set_bool('open_stdin', open_stdin)
        self.set_bool('stdin_once', stdin_once)
        self.env = Env(env)
        self.set_dict_str_str('labels', labels)
        self.set_str('working_dir', working_dir)
        self.set_bool('network', network)
        self.set_str('mac_address', mac_address)
        self.set_list_port('exposed_ports', exposed_ports)
        self.set_list_dict_str_str('volumes', volumes)
        self.set_int_or_str('stop_signal', stop_signal)

    def network_disabled(self):
        return not self.network

    JSON_FIELDS = (
        ('Image', (1, 14), 'image'),
        ('Cmd', (1, 14), 'command'),
        ('Entrypoint', (1, 15), 'entrypoint'),
        ('OnBuild', (1, 16), 'on_build'),
        ('Hostname', (1, 14), 'hostname'),
        ('Domainname', (1, 14), 'domainname'),
        ('User', (1, 14), 'user'),
        ('AttachStdin', (1, 14), 'attach_stdin'),
        ('AttachStdout', (1, 14), 'attach_stdout'),
        ('AttachStderr', (1, 14), 'attach_stderr'),
        ('Tty', (1, 14), 'tty'),
        ('OpenStdin', (1, 14), 'open_stdin'),
        ('StdinOnce', (1, 14), 'stdin_once'),
        ('Env', (1, 14), 'env'),
        ('Labels', (1, 18), 'labels'),
        ('WorkingDir', (1, 14), 'working_dir'),
        ('NetworkDisabled', (1, 14), 'network_disabled'),
        ('MacAddress', (1, 15), 'mac_address'),
        ('ExposedPorts', (1, 14), 'exposed_ports'),
        ('Volumes', (1, 14), 'volumes'),
        ('StopSignal', (1, 21), 'stop_signal'),
    )

    def json_object(self, api_version: Tuple[int, int]):
        d = {}
        for json_name, min_version, attr_name in self.JSON_FIELDS:
            if api_version < min_version:
                continue
            value = getattr(self, attr_name)
            if callable(value):
                value = value()
            if isinstance(value, Parameter):
                value = value.json_object(api_version)
            elif isinstance(value, collections.Sequence):
                value = [v.json_object()
                         if isinstance(v, Parameter)
                         else v
                         for v in value]
            if value is None:
                continue
            d[json_name] = value
        return d


class HostConfig(object):
    """Docker container host configuration.

    Arguments:
    memory -- memory limit (bytes)
    swap -- swap limit (bytes)
    cpu_shares -- cpu shares relative to other containers (integer value)
    cpu_period -- length of a cpu period (microseconds)
    cpuset_cpus -- cgroups cpuset.cpu to use
    cpuset_mems -- cgroups cpuset.mem to use
    blkio_weight -- relative block io weight (10 ... 1000)
    memory_swappiness -- memory swappiness behavior (10 ... 1000)
    oom_kill -- whether to enable OOM killer for container or not
    """

    def __init__(self,
                 binds: Sequence[VolumeBinding] = [],
                 links: Sequence[ContainerLink] = [],
                 lxc_conf: Mapping[str, str] = {},
                 memory: int = 0,
                 swap: int = 0,
                 memory_reservation: int = 0,
                 kernel_memory: int = 0,
                 cpu_shares: Optional[int] = None,
                 cpu_period: Optional[int] = None,
                 cpu_quota: Optional[int] = None,
                 cpuset_cpus: Optional[Cpuset] = None,
                 cpuset_mems: Optional[Cpuset] = None,
                 blkio_weight: Optional[int] = None,
                 memory_swappiness: Optional[int] = None,
                 oom_kill: bool = True,
                 port_bindings: Sequence[PortBinding] = None,
                 publish_all_ports: bool = False,
                 privileged: bool = False,
                 read_only_rootfs: bool = False,
                 dns: Sequence[IPAddress] = [],
                 dns_options: Sequence[str] = [],
                 dns_search: Sequence[str] = [],
                 extra_hosts: Sequence[HostnameIPMapping] = [],
                 group_add: Sequence[str] = [],
                 volumes_from: Sequence[VolumesFrom] = [],
                 cap_add: Sequence[str] = [],
                 cap_drop: Sequence[str] = [],
                 restart_policy: Mapping[str, Union[str, int]] = {},
                 network_mode: str = 'bridge',
                 devices: Sequence[DeviceToAdd] = [],
                 ulimits: Sequence[Ulimit] = [],
                 log_config: Optional[LogConfiguration] = None,
                 security_opt: Sequence[str] = [],
                 cgroup_parent: str ='',
                 volume_driver: str = ''):
        self.binds = list(binds or [])
        self.links = list(links or [])
        self.lxc_conf = dict(lxc_conf or {})
        if memory < 0:
            raise ValueError("'memory' limit cannot be negative: "
                             + str(memory))
        self.memory = memory
        if swap < 0:
            swap = -1
        elif swap and not memory > 0:
            raise ValueError("you must set 'memory' limit together with "
                             "'swap'")
        self.swap = swap
        if memory_reservation < 0:
            raise ValueError("'memory_reservation' limit cannot be negative: "
                             + str(memory_reservation))
        self.memory_reservation = memory_reservation
        if kernel_memory < 0:
            raise ValueError("'kernel_memory' limit cannot be negative: "
                             + str(kernel_memory))
        self.kernel_memory = kernel_memory
        if cpu_shares is not None and cpu_shares <= 0:
            raise ValueError("'cpu_shares' value must be positive: "
                             + str(cpu_shares))
        self.cpu_shares = cpu_shares
        self.cpu_period = cpu_period
        self.cpu_quota = cpu_quota
        self.cpuset_cpus = cpuset_cpus
        self.cpuset_mems = cpuset_mems
        if blkio_weight is not None and \
           (blkio_weight < 10 or blkio_weight > 1000):
            raise ValueError("'blkio_weight' must be between 10 and 1000: "
                             + str(blkio_weight))
        self.blkio_weight = blkio_weight
        if memory_swappiness is not None and \
           (memory_swappiness < 0 or memory_swappiness > 100):
            raise ValueError("'memory_swappiness' must be between 0 and 100: "
                             + str(swappiness))
        self.memory_swappiness = memory_swappiness
        self.oom_kill = oom_kill
        self.port_bindings = list(port_bindings or [])
        self.publish_all_ports = publish_all_ports
        self.privileged = privileged
        self.read_only_rootfs = read_only_rootfs
        self.dns = list(dns or [])
        self.dns_options = list(dns_options or [])
        self.dns_search = list(dns_search or [])
        self.extra_hosts = list(extra_hosts or [])
        self.group_add = list(group_add or [])
        self.volumes_from = list(volumes_from or [])
        self.cap_add = list(cap_add or [])
        self.cap_drop = list(cap_drop or [])
        self.restart_policy = dict(restart_policy or {})
        self.network_mode = network_mode
        self.devices = list(devices or [])
        self.ulimits = list(ulimits or [])
        self.security_opt = list(security_opt or [])
        self.log_config = log_config
        self.cgroup_parent = cgroup_parent
        self.volume_driver = volume_driver

    def oom_kill_disable(self):
        return not self.oom_kill

    def memory_swap(self):
        if self.swap < 0:
            return -1
        elif not self.swap:
            return 0
        else:
            return self.memory + self.swap

    JSON_FIELDS = (
        ('Binds', (1, 14), 'binds'),
        ('Links', (1, 14), 'links'),
        ('LxcConf', (1, 14), 'lxc_conf'),
        ('Memory', (1, 18), 'memory'),
        ('MemorySwap', (1, 18), 'memory_swap'),
        ('MemoryReservation', (1, 21), 'memory_reservation'),
        ('KernelMemory', (1, 21), 'kernel_memory'),
        ('CpuShares', (1, 18), 'cpu_shares'),
        ('CpuPeriod', (1, 19), 'cpu_period'),
        ('CpuQuota', (1, 19), 'cpu_quota'),
        ('CpusetCpus', (1, 18), 'cpuset_cpus'),
        ('CpusetMems', (1, 19), 'cpuset_mems'),
        ('BlkioWeight', (1, 19), 'blkio_weight'),
        ('MemorySwappiness', (1, 20), 'memory_swappiness'),
        ('OomKillDisable', (1, 19), 'oom_kill_disable'),
        ('PortBindings', (1, 14), 'port_bindings'),
        ('PublishAllPorts', (1, 14), 'publish_all_ports'),
        ('Privileged', (1, 14), 'privileged'),
        ('ReadonlyRootfs', (1, 17), 'read_only_rootfs'),
        ('Dns', (1, 14), 'dns'),
        ('DnsOptions', (1, 21), 'dns_options'),
        ('DnsSearch', (1, 15), 'dns_search'),
        ('ExtraHosts', (1, 15), 'extra_hosts'),
        ('GroupAdd', (1, 20), 'group_add'),
        ('VolumesFrom', (1, 14), 'volumes_from'),
        ('CapAdd', (1, 14), 'cap_add'),
        ('CapDrop', (1, 14), 'cap_drop'),
        ('RestartPolicy', (1, 15), 'restart_policy'),
        ('NetworkMode', (1, 15), 'network_mode'),
        ('Devices', (1, 15), 'devices'),
        ('Ulimits', (1, 18), 'ulimits'),
        ('LogConfig', (1, 18), 'log_config'),
        ('SecurityOpt', (1, 17), 'security_opt'),
        ('CgroupParent', (1, 18), 'cgroup_parent'),
        ('VolumeDriver', (1, 21), 'volume_driver'),
    )

    def json_object(self, api_version: Tuple[int, int]):
        d = {}
        for json_name, min_version, attr_name in self.JSON_FIELDS:
            if api_version < min_version:
                continue
            value = getattr(self, attr_name)
            if callable(value):
                value = value()
            if isinstance(value, Parameter):
                value = value.json_object(api_version)
            elif isinstance(value, collections.Sequence):
                value = [v.json_object()
                         if isinstance(v, Parameter)
                         else v
                         for v in value]
            if value is None:
                continue
            d[json_name] = value
        return d














__all__ += [
    'set_integer', 'set_boolean', 'set_string', 'set_list_of_strings',
    'set_string_or_list_of_strings', 'set_dict_of_strings',
    'set_container_name', 'set_repository_name', 'set_repository_tag',
    'set_image_name', 'set_hostname', 'set_domainname', 'set_user_name',
    'set_cpuset_list', 'set_list_of_ports',
    'set_host_config']


def set_integer(d, name, value, min=None, max=None):
    if value is None:
        return
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError('not integer value: %s' % type(value))
    if min is not None and value < min:
        raise ValueError('value too small: %d' % value)
    if max is not None and value > max:
        raise ValueError('value too big: %d' % value)
    d[name] = value


def set_boolean(d, name, value, ignore=[]):
    if value is None:
        return
    if not isinstance(value, bool):
        raise TypeError('not boolean value: %s' % type(value))
    if value in ignore:
        return
    d[name] = value


def set_string(d, name, value):
    if value is None:
        return
    if not isinstance(value, str):
        raise TypeError('value must be str: %s' % type(value))
    d[name] = value


def set_list_of_strings(d, name, value):
    if value is None:
        return
    if isinstance(value, list):
        for element in value:
            if not isinstance(element, str):
                raise ValueError('must be list of str')
    else:
        raise TypeError('must be list of str')
    d[name] = value


def set_string_or_list_of_strings(d, name, value):
    if value is None:
        return
    if isinstance(value, str):
        pass
    elif isinstance(value, list):
        for element in value:
            if not isinstance(element, str):
                raise ValueError('must be str or list of str')
    else:
        raise TypeError('must be str or list of str')
    d[name] = value


def set_dict_of_strings(d, name, value):
    if value is None:
        return
    if isinstance(value, dict):
        for key, element in value.items():
            if not isinstance(element, str):
                raise ValueError('must be dict of str')
    else:
        raise TypeError('must be dict of str')
    d[name] = value


CONTAINER_NAME_RE = re.compile(r'/?[a-zA-Z0-9_-]+$')


def set_container_name(d, name, value):
    if value is None:
        return
    if not isinstance(value, str):
        raise TypeError('container name must be str: %s' % type(value))
    if not CONTAINER_NAME_RE.match(value):
        raise ValueError('invalid container name: %s' % value)
    d[name] = value


REPOSITORY_NAME_RE = re.compile(r'[a-z0-9-_.]+$')


def set_repository_name(d, name, value):
    if value is None:
        return
    if not isinstance(value, str):
        raise TypeError('repository name must be str: %s' % type(value))
    if not REPOSITORY_NAME_RE.match(value):
        raise ValueError('invalid repository name: %s' % value)
    d[name] = value


REPOSITORY_TAG_RE = re.compile(r'[a-zA-Z0-9-_.]+$')


def set_repository_tag(d, name, value):
    if value is None:
        return
    if not isinstance(value, str):
        raise TypeError('repository tag must be str: %s' % type(value))
    if not REPOSITORY_TAG_RE.match(value):
        raise ValueError('invalid repository tag: %s' % value)
    d[name] = value


IMAGE_NAME_RE = re.compile(r'%s(:%s)?$'%(
    REPOSITORY_NAME_RE.pattern[:-1], REPOSITORY_TAG_RE.pattern[:-1]))


def set_image_name(d, name, value):
    if value is None:
        return
    if not isinstance(value, str):
        raise TypeError('image_name must be str: %s' % type(value))
    if not IMAGE_NAME_RE.match(value):
        raise ValueError('invalid image name: %s' % value)
    d[name] = value


HOSTNAME_RE = re.compile(r'[a-z0-9]([a-z0-9-]*[a-z0-9])?$')


def set_hostname(d, name, value):
    if value is None:
        return
    if not isinstance(value, str):
        raise TypeError('hostname must be str: %s' % type(value))
    if not HOSTNAME_RE.match(value):
        raise ValueError('invalid hostname: %s' % value)
    d[name] = value


DOMAINNAME_RE = re.compile('%s(\.%s)*$' % (
    HOSTNAME_RE.pattern[:-1], HOSTNAME_RE.pattern[:-1]))


def set_domainname(d, name, value):
    if value is None:
        return
    if not isinstance(value, str):
        raise TypeError('domain name must be str: %s' % type(value))
    if not DOMAINNAME_RE.match(value):
        raise ValueError('invalid domain name: %s' % value)
    d[name] = value



USER_NAME_RE = re.compile(r'[a-z0-9][a-z0-9_-]*$')


def set_user_name(d, name, value):
    if value is None:
        return
    if not isinstance(value, str):
        raise TypeError('domain name must be str: %s' % type(value))
    if not USER_NAME_RE.match(value):
        raise ValueError('invalid user name: %s' % value)
    d[name] = value


CPUSET_LIST_RE = re.compile(r'(\d|[1-9]\d+)([,-](\d|[1-9]\d+))*$')


def set_cpuset_list(d, name, value):
    if value is None:
        return
    if not isinstance(value, str):
        raise TypeError('cpuset list value must be str: %s' % type(value))
    if not CPUSET_LIST_RE.match(value):
        raise ValueError('invalid cpuset list: %s' % value)
    d[name] = value


PORT_RE = re.compile(r'[1-9]\d*/(tcp|udp)$')


def set_list_of_ports(d, name, value):
    if value is None:
        return
    if not isinstance(value, list):
        raise TypeError('value must be list of str: %s' % type(value))
    for element in value:
        if not isinstance(element, str):
            raise TypeError('value must be list of str: %s' % type(value))
        if not PORT_RE.match(element):
            raise ValueError('invalid port specification: %s' % (element))
    d[name] = value


def set_host_config(d, name, value, api_version):
    if value is None:
        return
    if not isinstance(value, HostConfig):
        raise TypeError('value must be HostConfig: %s' % type(value))
    d[name] = value.json_object(api_version)
