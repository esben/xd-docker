"""Module containing DockerClient and associated exceptions."""

import logging
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


from ipaddress import IPv4Address, IPv6Address
from typing import Optional, Union, Mapping, Sequence, Tuple
import re
import collections


__all__ = ['HostConfig', 'IPAddress', 'VolumeBinding', 'ContainerLink',
           'PortBinding', 'HostnameIPMapping', 'VolumesFrom', 'DeviceToAdd',
           'Ulimit', 'LogConfiguration']


IPAddress = Union[IPv4Address, IPv6Address]


class HostConfigAttribute(object):

    def __str__(self):
        return str(self.json_object())


class VolumeBinding(HostConfigAttribute):
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

    def json_object(self):
        if not host_path:
            return self.container_path
        if self.ro:
            return '%s:%s:ro' % (self.host_path, self.container_path)
        else:
            return '%s:%s' % (self.host_path, self.container_path)


class ContainerLink(HostConfigAttribute):
    """Docker container link."""

    def __init__(self, name: str, alias: str):
        self.name = name
        self.alias = alias

    def json_object(self):
        return '%s:%s' % (self.name, self.alias)


class Cpuset(HostConfigAttribute):
    """List of CPUs or memory nodes."""

    CPUSET_LIST_RE = re.compile(r'(\d|[1-9]\d+)([,-](\d|[1-9]\d+))*$')

    def __init__(self, cpuset: str):
        if not cpuset:
            self.cpuset = None
        elif not self.CPUSET_LIST_RE.match(cpuset):
            raise ValueError('invalid cpuset: %s' % cpuset)
        else:
            self.cpuset = cpuset

    def json_object(self):
        return self.cpuset


class PortBinding(HostConfigAttribute):
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

    def json_object(self):
        host_binding = {'HostPort': str(self.host_port)}
        if self.host_ip is not None:
            host_binding['HostIp'] = str(self.host_ip)
        return {'%d/%s' % (self.port, self.protocol): [host_binding]}


class HostnameIPMapping(HostConfigAttribute):
    """Hostname to IP address mapping."""

    def __init__(self, hostname: str, ip: IPAddress):
        self.hostname = hostname
        self.ip = ip

    def json_object(self):
        return '%s:%s' % (self.hostname, self.ip)


class VolumesFrom(HostConfigAttribute):
    """Docker container to inherit volumes from."""

    def __init__(self, name: str, ro: bool = False):
        self.name = name
        self.ro = ro

    def json_object(self):
        return '%s:%s' % (self.name, 'ro' if self.ro else 'rw')


class DeviceToAdd(HostConfigAttribute):
    """Device to add to docker container."""

    def __init__(self, path_on_host: str,
                 path_in_container: Optional[str] = None,
                 cgroup_permissions: str = 'mrw'):
        self.path_on_host = path_on_host
        if path_in_container is None:
            path_in_container = path_on_host
        self.path_in_container = path_in_container
        self.cgroup_permissions = cgroup_permissions

    def json_object(self):
        return {'PathOnOhost': self.path_on_host,
                'PathInContainer': self.path_in_container,
                'CgroupPermissions': self.cgroup_permissions}


class Ulimit(HostConfigAttribute):
    """Ulimit setting."""

    def __init__(self, name: str, soft: int, hard: Optional[int] = None):
        self.name = name
        self.soft = soft
        if hard is None:
            hard = soft
        self.hard = hard

    def json_object(self):
        return {'Name': self.name,
                'Soft': self.soft,
                'Hard': self.hard}


class LogConfiguration(HostConfigAttribute):
    """Docker container log configuration."""

    AVAILABLE_TYPES = (
        'json-file', 'syslog', 'journald', 'gelf', 'awslogs', 'none')

    def __init__(self, type: str, config: Mapping[str, str]):
        if type not in self.AVAILABLE_TYPES:
            raise ValueError("invalid type: " + type)
        self.type = type
        self.config = dict(config)

    def json_object(self):
        return {'Type': self.type, 'Config': self.config}


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
            value = getattr(self, attr_name)
            if callable(value):
                value = value()
            if isinstance(value, HostConfigAttribute):
                value = value.json_object()
            elif isinstance(value, collections.Sequence):
                value = [v.json_object()
                         if isinstance(v, HostConfigAttribute)
                         else v
                         for v in value]
            if value is None:
                continue
            if api_version < min_version:
                continue
            d[json_name] = value
        return d
