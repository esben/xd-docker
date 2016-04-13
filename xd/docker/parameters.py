"""Module containing helper classes and functions for handling Docker Remote
API parameters."""

import collections
import re

from typing import Any, Optional, Union, Mapping, Sequence, Tuple, Dict
import ipaddress

import logging
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

IPAddress = Union[ipaddress.IPv4Address, ipaddress.IPv6Address]
Command = Union[str, Sequence[str]]
Signal = Union[int, str]
ApiVersion = Tuple[int, int]


__all__ = ['IPAddress', 'Command', 'Signal', 'ApiVersion',
           'json_update',
           'Parameter',
           'Repository', 'ContainerName',
           'Env', 'Port', 'PortBinding', 'VolumeMount', 'VolumeBinding',
           'ContainerLink', 'Cpuset',
           'Hostname', 'Domainname', 'MacAddress', 'Username',
           'HostnameIPMapping', 'VolumesFrom', 'RestartPolicy',
           'DeviceToAdd', 'Ulimit', 'LogConfiguration',
           'RegistryAuth', 'RegistryAuthConfig',
           'ContainerConfig', 'HostConfig']


def json_update(obj: Dict[str, Any], values: Dict[str, Any],
                json_fields: Sequence[Tuple[str, Tuple[int, int], str]],
                api_version: Optional[ApiVersion] = None):
    """Update JSON object (dict).

    This function is used to update a JSON object (a dict) with name/value
    pairs from the values argument, based on the specification in json_fields
    and api_version arguments.

    Arguments:
      obj: JSON object to update.
      values: Name/value pairs to update with.
      json_fields: Specification of supported JSON object name/value pairs,
        including information on which API version they are supported in.
      api_version: API version to update for.
    """
    for json_name, min_version, value_name in json_fields:
        if isinstance(values, dict):
            value = values.get(value_name)
        else:
            value = getattr(values, value_name)
        if isinstance(value, str):
            pass
        elif isinstance(value, Parameter):
            value = value.json(api_version)
        elif isinstance(value, collections.Sequence):
            value = [v.json()
                     if isinstance(v, Parameter)
                     else str(v) if isinstance(v, ipaddress._IPAddressBase)
                     else v
                     for v in value]
        if value is None:
            continue
        if api_version and api_version < min_version:
            print(json_name, value)
            raise ValueError('%s not supported by Remote API %s' % (
                json_name, '.'.join([str(i) for i in api_version])))
        obj[json_name] = value
    return obj


class Parameter(object):
    """Base class for all XD Docker parameter classes."""

    def __str__(self):
        return str(self.json())

    def json(self, api_version: Optional[ApiVersion] = None):
        """Return Docker Remote API JSON representation.

        Arguments:
          api_version: Docker Remote API version.
        """
        raise NotImplementedError


class Repository(Parameter):
    """Repository name (and optionally tag) parameter.

    A Repository instance is used to represent a Docker repository name, or
    repository name and tag.

    Attributes:
      name (str): Repository name.
      tag (Optional[str]): Repository tag.
    """
    NAME_RE = re.compile(r'[a-z0-9-_.]+$')
    TAG_RE = re.compile(r'[a-zA-Z0-9-_.]+$')
    NAME_AND_TAG_RE = re.compile(r'(%s):(%s)?$' % (
        NAME_RE.pattern[:-1], TAG_RE.pattern[:-1]))

    def __init__(self, repo: str):
        """
        Arguments:
          repo: Repository name, or name and tag (separated by ':').
        """
        if self.NAME_RE.match(repo):
            self.name = repo
            self.tag = None
            return
        name_and_tag = self.NAME_AND_TAG_RE.match(repo)
        if name_and_tag:
            self.name = name_and_tag.group(1)
            self.tag = name_and_tag.group(2)
            return
        raise ValueError('invalid repository name: %s' % repo)

    def json(self, api_version: Optional[ApiVersion] = None):
        if self.tag:
            return "%s:%s" % (self.name, self.tag)
        else:
            return self.name


class ContainerName(Parameter):
    """Container name parameter.

    A ContainerName instance is used to represent a Docker container name.

    Attributes:
      name (str): Container name.
    """

    NAME_RE = re.compile(r'/?[a-zA-Z0-9_-]+$')

    def __init__(self, name: str):
        """
        Arguments:
          name: Container name
        """
        if self.NAME_RE.match(name):
            self.name = name
            return
        raise ValueError('invalid container name: %s' % name)

    def json(self, api_version: Optional[ApiVersion] = None):
        return self.name


class Env(Parameter):
    """Environment variables.

    An Environment instance contains the environment variables for a Docker
    container.

    Attributes:
      env (Mapping[str, str]): Environment variables, name/value pairs.
    """

    KEY_RE = re.compile(r'[a-zA-Z_][a-zA-Z0-9_]*$')

    def __init__(self, env: Optional[Mapping[str, str]]=None):
        """
        Arguments:
          env: Environment variables, name/value pairs.
        """
        self.env = env
        if env:
            for k in env:
                if not isinstance(k, str):
                    raise TypeError('Env variable name must be string: %s'
                                    % type(k))
                if not self.KEY_RE.match(k):
                    raise ValueError('Invalid Env variable name: %s' % k)

    def json(self, api_version: Optional[ApiVersion] = None):
        if self.env is None:
            return None
        else:
            return ['%s=%s' % (k, v) for k, v in self.env.items()]


class Port(Parameter):
    """Network port.

    A Port instance represents a network port (TCP or UDP).

    Attributes:
      port (int): Port number.
      protocol (str): Protocol ('tcp' or 'udp').
    """

    def __init__(self, port: int, protocol: str = 'tcp'):
        """
        Arguments:
          port: Port number.
          protocol: Protocol ('tcp' or 'udp').
        """
        if port <= 0 or port > 65535:
            raise ValueError('port must be > 0 and <= 65535')
        self.port = port
        if protocol not in ('tcp', 'udp'):
            raise ValueError("protocol must be either 'tcp' or 'udp'")
        self.protocol = protocol

    def json(self, api_version: Optional[ApiVersion] = None):
        return '%d/%s' % (self.port, self.protocol)


class PortBinding(Parameter):
    """Docker container port binding.

    A PortBinding instance represents a binding of a network port of a Docker
    container to a host port.

    Attributes:
      port (int): Container port number (1 ... 65535).
      protocol (str): Protocol ('tcp' or 'udp').
      host_ip (Optional[IPAddress]): Host IP address.
      host_port (int): Host port number (1 ... 65535).
    """

    def __init__(self, port: int, protocol: str = 'tcp',
                 host_ip: Optional[IPAddress] = None,
                 host_port: Optional[int] = None):
        """
        Arguments:
          port: Container port number.
          protocol: Protocol ('tcp' or 'udp').
          host_ip: Host IP address.
          host_port: Host port number (defaults to container port number).
        """
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

    def json(self, api_version: Optional[ApiVersion] = None):
        host_binding = {'HostPort': str(self.host_port)}
        if self.host_ip is not None:
            host_binding['HostIp'] = str(self.host_ip)
        return {'%d/%s' % (self.port, self.protocol): [host_binding]}


class VolumeMount(Parameter):
    """Volume mount point.

    A VolumeMount instance represents a container mount point.

    Attributes:
      source (str): Source path.
      destination (str): Destination path.
      ro (bool): Read-only mount.
      label_mode (str): SELinux label mode ('', 'z', or 'Z').
    """

    def __init__(self, source: str, destination: str, ro: bool = False,
                 label_mode: Optional[str] = None):
        """
        Arguments:
          source: Host path.
          destination: Container path.
          ro: Read-only mount.
          label_mode: SELinux label mode ('z' or 'Z').
        """
        self.source = source
        self.destination = destination
        self.ro = ro
        self.label_mode = label_mode or ''

    def json(self, api_version: Optional[ApiVersion] = None):
        mode = 'ro' if self.ro else 'rw'
        if self.label_mode:
            mode += ',' + self.label_mode
        return {'Source': self.source,
                'Destination': self.destination,
                'RW': not self.ro,
                'Mode': mode}


class VolumeBinding(Parameter):
    """Volume binding.

    A VolumeBinding instance represents a volume binding for a container.  The
    binding can either be to a new volume, an existing host path, or a volume
    provided by a Docker volume plugin.

    Attributes:
      container_path (str): Container path to bind the volume to.
      volume (Optional[str]): Host path or volume name, identifying the volume
        to bind to.
      ro (bool): Read-only mount.
    """

    def __init__(self, container_path: str, volume: Optional[str] = None,
                 ro: bool = False):
        """
        Arguments:
          container_path: Container path to bind the volume to.
          volume: Host path or volume name, identifying the volume
            to bind to.  Host path must start with a '/'.  Volume name must
            not begin with a '/'.
          ro: Read-only mount.
        """
        if container_path == '':
            raise ValueError('invalid container_path')
        if volume == '':
            raise ValueError('invalid volume')
        if ro and not volume:
            raise ValueError('volume required when ro=True')
        self.container_path = container_path
        if volume is None:
            self.volume = None
        else:
            self.volume = volume
        self.ro = ro

    def json(self, api_version: Optional[ApiVersion] = None):
        if not self.volume:
            return self.container_path
        if self.ro:
            return '%s:%s:ro' % (self.volume, self.container_path)
        else:
            return '%s:%s' % (self.volume, self.container_path)


class ContainerLink(Parameter):
    """Container link.

    A ContainerLink instance represents a link to another container.

    Attributes:
      name (str): Name of container to link to.
      alias (str): Alias to use for linked container.
    """

    def __init__(self, name: str, alias: str):
        """
        Arguments:
          name: Name of container to link to.
          alias: Alias to use for linked container.
        """
        self.name = name
        self.alias = alias

    def json(self, api_version: Optional[ApiVersion] = None):
        return '%s:%s' % (self.name, self.alias)


class Cpuset(Parameter):
    """List of CPUs.

    A Cpuset instance represents a set of CPU or memory nodes, for use when
    specifying where to run a container.

    Attributes:
      cpuset (str): Cpuset specification.
    """

    CPUSET_LIST_RE = re.compile(r'(\d|[1-9]\d+)([,-](\d|[1-9]\d+))*$')

    def __init__(self, cpuset: str):
        """
        Arguments:
          cpuset: Cpuset specification.  See `cpuset(7)`_ for syntax.

        .. _cpuset(7): http://man7.org/linux/man-pages/man7/cpuset.7.html
        """
        if not self.CPUSET_LIST_RE.match(cpuset):
            raise ValueError('invalid cpuset: %s' % cpuset)
        self.cpuset = cpuset

    def json(self, api_version: Optional[ApiVersion] = None):
        return self.cpuset


class Hostname(Parameter):
    """Hostname.

    A Hostname instance represents a network hostname.  A hostname must not
    contain dots ('.').  To specify a fully qualified domain name, use
    :class:`.Domainname`.

    Attributes:
      hostname (str): Hostname.
    """

    HOSTNAME_RE = re.compile(r'[a-z0-9]([a-z0-9-]*[a-z0-9])?$')

    def __init__(self, hostname: str):
        """
        Arguments:
          hostname: Hostname.
        """
        if not self.HOSTNAME_RE.match(hostname):
            raise ValueError('invalid hostname: %s' % hostname)
        self.hostname = hostname

    def json(self, api_version: Optional[ApiVersion] = None):
        return self.hostname


class Domainname(Hostname):
    """Domain name.

    A Domainname instance represents a network domain name.

    Attributes:
      domainname (str): Domain name.
    """

    DOMAINNAME_RE = re.compile('%s(\.%s)*$' % (
        Hostname.HOSTNAME_RE.pattern[:-1], Hostname.HOSTNAME_RE.pattern[:-1]))

    def __init__(self, domainname: str):
        """
        Arguments:
          domainname: Domain name.
        """
        if not self.DOMAINNAME_RE.match(domainname):
            raise ValueError('invalid domainname: %s' % domainname)
        self.domainname = domainname

    def json(self, api_version: Optional[ApiVersion] = None):
        return self.domainname


class MacAddress(Hostname):
    """Ethernet MAC address."""

    MACADDRESS_RE = re.compile('[0-9a-fA-F]{2}(:[0-9a-fA-F]{2}){5}$')

    def __init__(self, addr: str):
        if not self.MACADDRESS_RE.match(addr):
            raise ValueError('invalid MAC address: %s' % addr)
        self.addr = addr

    def json(self, api_version: Optional[ApiVersion] = None):
        return self.addr


class Username(Hostname):
    """User name."""

    USERNAME_RE = re.compile(r'[a-z0-9][a-z0-9_-]*$')

    def __init__(self, username: str):
        if not self.USERNAME_RE.match(username):
            raise ValueError('invalid username: %s' % username)
        self.username = username

    def json(self, api_version: Optional[ApiVersion] = None):
        return self.username


class HostnameIPMapping(Parameter):
    """Hostname to IP address mapping."""

    def __init__(self, hostname: Union[Hostname, str],
                 ip: Union[IPAddress, str]):
        if isinstance(hostname, Hostname):
            self.hostname = hostname
        else:
            self.hostname = Domainname(hostname)
        if isinstance(ip, ipaddress._IPAddressBase):
            self.ip = ip
        else:
            self.ip = ipaddress.ip_address(ip)

    def json(self, api_version: Optional[ApiVersion] = None):
        return '%s:%s' % (self.hostname.json(api_version), self.ip)


class VolumesFrom(Parameter):
    """Docker container to inherit volumes from."""

    def __init__(self, name: Union[ContainerName, str],
                 ro: Optional[bool] = None):
        if isinstance(name, str):
            name = ContainerName(name)
        self.name = name
        self.ro = ro

    def json(self, api_version: Optional[ApiVersion] = None):
        if self.ro is None:
            return self.name.json(api_version)
        else:
            return '%s:%s' % (self.name.json(api_version),
                              'ro' if self.ro else 'rw')


class RestartPolicy(Parameter):
    """Restart policy for when the container exits."""

    def __init__(self, policy: str, maximum_retry_count: Optional[int] = None):
        if policy not in ('always', 'unless-stopped', 'on-failure'):
            raise ValueError('invalid policy value: %s' % policy)
        self.policy = policy
        if policy == 'on-failure':
            if maximum_retry_count is None:
                raise TypeError('RestartPolicy("on-failure")' +
                                ' requires maximum_retry_count argument')
            if maximum_retry_count < 0:
                raise ValueError('maximum_retry_count must be positive')
            self.maximum_retry_count = maximum_retry_count

    def json(self, api_version: Optional[ApiVersion] = None):
        d = {'Name': self.policy}
        if self.policy == 'on-failure':
            d['MaximumRetryCount'] = self.maximum_retry_count
        return d


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

    def json(self, api_version: Optional[ApiVersion] = None):
        return {'PathOnHost': self.path_on_host,
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

    def json(self, api_version: Optional[ApiVersion] = None):
        return {'Name': self.name,
                'Soft': self.soft,
                'Hard': self.hard}


class LogConfiguration(Parameter):
    """Docker container log configuration."""

    AVAILABLE_TYPES = (
        'json-file', 'syslog', 'journald', 'gelf', 'awslogs', 'none')

    def __init__(self, type: str, config: Optional[Mapping[str, str]]=None):
        if type not in self.AVAILABLE_TYPES:
            raise ValueError("invalid type: " + type)
        self.type = type
        if config is None:
            self.config = config
        else:
            self.config = dict(config)

    def json(self, api_version: Optional[ApiVersion] = None):
        return {'Type': self.type, 'Config': self.config}


class RegistryAuth(object):
    """Docker registry authentication for a single registry."""

    def __init__(self, url: str, username: str, password: str):
        self.url = url
        self.username = username
        self.password = password

    def json(self, api_version: Optional[Tuple[int, int]]=None):
        return {self.url: {
            'username': self.username,
            'password': self.password}}


class RegistryAuthConfig(object):
    """Docker registry authentication configuration."""

    def __init__(self, registry_auths: Sequence[RegistryAuth]):
        self.registry_auths = registry_auths

    def json(self, api_version: Optional[Tuple[int, int]]=None):
        d = {}
        for registry_auth in self.registry_auths:
            d.update(registry_auth.json(api_version))
        return d


class ContainerConfig(Parameter):
    """Docker container configuration.

    Arguments:
      image: Image create container from
      command: Command to run (string or list of strings)
      entrypoint: Container entrypoint (string or list of strings)
      on_build: Trigger instructions to be executed later (list of strings)
      hostname: Hostname to use for the container
      domainname: Domain name to use for the container
      user: User inside the container (user name)
      attach_stdin: Attach to stdin (boolean)
      attach_stdout: Attach to stdout (boolean)
      attach_stderr: Attach to stderr (boolean)
      tty: Attach standard streams to a tty (boolean)
      open_stdin: Open stdin (boolean)
      stdin_once: Close stdin after the client disconnects (boolean)
      env: Environment variables (dict)
      labels: Labels to set on container (dict)
      working_dir: Working directory for command to run in (string)
      mac_address: MAC address (string)
      network: Whether to enable networking in the container (boolean)
      exposed_ports: Exposed ports (list of ports)
      volumes: FIXME
      stop_signal: Signal to stop container (int or string)
    """

    # TODO: Figure out how to handle Mounts and Volumes parameters.  It seems
    # like Volumes parameter were replaced by Mounts in 1.20, and the Mounts
    # parameter has more features.  So maybe we should support mounts
    # argument, and then generate Volumes for older API.

    def __init__(self,
                 image: str,
                 command: Optional[Command]=None,
                 entrypoint: Optional[Command]=None,
                 on_build: Optional[Sequence[str]]=None,
                 hostname: Optional[Union[Hostname, str]]=None,
                 domainname: Optional[Union[Domainname, str]]=None,
                 user: Optional[Union[Username, str]]=None,
                 attach_stdin: Optional[bool]=None,
                 attach_stdout: Optional[bool]=None,
                 attach_stderr: Optional[bool]=None,
                 tty: Optional[bool]=None,
                 open_stdin: Optional[bool]=None,
                 stdin_once: Optional[bool]=None,
                 env: Optional[Union[Env, Mapping[str, str]]]=None,
                 labels: Optional[Mapping[str, str]]=None,
                 working_dir: Optional[str]=None,
                 network: bool=True,
                 mac_address: Optional[Union[MacAddress, str]]=None,
                 exposed_ports: Optional[Sequence[Port]]=None,
                 volumes: Optional[Sequence[Mapping[str, str]]]=None,
                 stop_signal: Optional[Union[int, str]]=None):
        self.image = image
        self.command = command
        self.entrypoint = entrypoint
        self.on_build = on_build
        if isinstance(hostname, str):
            hostname = Hostname(hostname)
        elif isinstance(hostname, Domainname):
            raise TypeError('hostname cannot be Domainname')
        self.hostname = hostname
        if isinstance(domainname, str):
            hostname = Domainname(domainname)
        self.domainname = domainname
        if isinstance(user, str):
            user = Username(user)
        self.user = user
        self.attach_stdin = attach_stdin
        self.attach_stdout = attach_stdout
        self.attach_stderr = attach_stderr
        self.tty = tty
        self.open_stdin = open_stdin
        self.stdin_once = stdin_once
        if isinstance(env, collections.Mapping):
            env = Env(env)
        self.env = env
        self.labels = labels
        self.working_dir = working_dir
        self.network = network
        if isinstance(mac_address, str):
            mac_address = MacAddress(mac_address)
        self.mac_address = mac_address
        self.exposed_ports = exposed_ports
        self.volumes = volumes
        self.stop_signal = stop_signal

    @property
    def network_disabled(self):
        print('network_disabled()', self.network)
        if self.network is False:
            return True
        else:
            return None

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

    def json(self, api_version: Tuple[int, int]=(1, 14)):
        return json_update({}, self, self.JSON_FIELDS, api_version)


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
                 binds: Optional[Sequence[VolumeBinding]]=None,
                 links: Optional[Sequence[ContainerLink]]=None,
                 lxc_conf: Optional[Mapping[str, str]]=None,
                 memory: Optional[int]=None,
                 swap: Optional[int]=None,
                 memory_reservation: Optional[int]=None,
                 kernel_memory: Optional[int]=None,
                 cpu_shares: Optional[int]=None,
                 cpu_period: Optional[int]=None,
                 cpu_quota: Optional[int]=None,
                 cpuset_cpus: Optional[Union[Cpuset, str]]=None,
                 cpuset_mems: Optional[Union[Cpuset, str]]=None,
                 blkio_weight: Optional[int]=None,
                 memory_swappiness: Optional[int]=None,
                 oom_kill: Optional[bool]=None,
                 port_bindings: Sequence[PortBinding]=None,
                 publish_all_ports: Optional[bool]=None,
                 privileged: Optional[bool]=None,
                 read_only_rootfs: Optional[bool]=None,
                 dns: Optional[Sequence[IPAddress]]=None,
                 dns_options: Optional[Sequence[str]]=None,
                 dns_search: Optional[Sequence[str]]=None,
                 extra_hosts: Optional[Sequence[
                     Union[HostnameIPMapping, str]]]=None,
                 group_add: Optional[Sequence[str]]=None,
                 volumes_from: Optional[Sequence[
                     Union[VolumesFrom, str]]]=None,
                 cap_add: Optional[Sequence[str]]=None,
                 cap_drop: Optional[Sequence[str]]=None,
                 restart_policy: Optional[RestartPolicy]=None,
                 network_mode: Optional[str]=None,
                 devices: Optional[Sequence[
                     Union[DeviceToAdd, str]]]=None,
                 ulimits: Optional[Sequence[Ulimit]]=None,
                 log_config: Optional[LogConfiguration]=None,
                 security_opt: Optional[Sequence[str]]=None,
                 cgroup_parent: Optional[str]=None,
                 volume_driver: Optional[str]=None,
                 shm_size: Optional[int]=None):
        if binds is not None:
            binds = list(binds)
        self.binds = binds
        if links is not None:
            links = list(links)
        self.links = links
        if lxc_conf is not None:
            lxc_conf = dict(lxc_conf)
        self.lxc_conf = lxc_conf
        if isinstance(memory, int) and memory < 0:
            raise ValueError("'memory' limit cannot be negative: " +
                             str(memory))
        self.memory = memory
        if isinstance(swap, int) and swap < 0:
            swap = -1
        elif swap and not memory:
            raise ValueError("you must set 'memory' limit together with "
                             "'swap'")
        elif swap == 0:
            raise ValueError("'swap' cannot be zero")
        self.swap = swap
        if isinstance(memory_reservation, int) and memory_reservation < 0:
            raise ValueError(
                "'memory_reservation' limit cannot be negative: " +
                str(memory_reservation))
        self.memory_reservation = memory_reservation
        if isinstance(kernel_memory, int) and kernel_memory < 0:
            raise ValueError("'kernel_memory' limit cannot be negative: " +
                             str(kernel_memory))
        self.kernel_memory = kernel_memory
        if cpu_shares is not None and cpu_shares <= 0:
            raise ValueError("'cpu_shares' value must be positive: " +
                             str(cpu_shares))
        self.cpu_shares = cpu_shares
        if cpu_period is not None and cpu_period <= 0:
            raise ValueError("'cpu_period' value must be positive: " +
                             str(cpu_period))
        self.cpu_period = cpu_period
        if cpu_quota is not None and cpu_quota <= 0:
            raise ValueError("'cpu_quota' value must be positive: " +
                             str(cpu_quota))
        self.cpu_quota = cpu_quota
        if isinstance(cpuset_cpus, str):
            cpuset_cpus = Cpuset(cpuset_cpus)
        self.cpuset_cpus = cpuset_cpus
        if isinstance(cpuset_mems, str):
            cpuset_mems = Cpuset(cpuset_mems)
        self.cpuset_mems = cpuset_mems
        if blkio_weight is not None and \
           (blkio_weight < 10 or blkio_weight > 1000):
            raise ValueError("'blkio_weight' must be between 10 and 1000: " +
                             str(blkio_weight))
        self.blkio_weight = blkio_weight
        if memory_swappiness is not None and \
           (memory_swappiness < 0 or memory_swappiness > 100):
            raise ValueError(
                "'memory_swappiness' must be between 0 and 100: " +
                str(memory_swappiness))
        self.memory_swappiness = memory_swappiness
        self.oom_kill = oom_kill
        if port_bindings is not None:
            port_bindings = list(port_bindings)
        self.port_bindings = port_bindings
        self.publish_all_ports = publish_all_ports
        self.privileged = privileged
        self.read_only_rootfs = read_only_rootfs
        if dns is not None:
            dns = [ipaddress.ip_address(ip)
                   if isinstance(ip, str) else ip
                   for ip in dns]
        self.dns = dns
        if dns_options is not None:
            dns_options = list(dns_options)
        self.dns_options = dns_options
        if dns_search is not None:
            dns_search = list(dns_search)
        self.dns_search = dns_search
        if extra_hosts is not None:
            extra_hosts = list(extra_hosts)
            for index, host in enumerate(extra_hosts):
                if isinstance(host, str):
                    host = host.split(':')
                    if len(host) != 2:
                        raise ValueError('invalid extra_hosts str value: %s' %
                                         extra_hosts[index])
                    extra_hosts[index] = HostnameIPMapping(*host)
        self.extra_hosts = extra_hosts
        if group_add is not None:
            group_add = list(group_add)
        self.group_add = group_add
        if volumes_from is not None:
            volumes_from = list(volumes_from)
            for index, vf in enumerate(volumes_from):
                if isinstance(vf, str):
                    volumes_from[index] = VolumesFrom(vf)
        self.volumes_from = volumes_from
        if cap_add is not None:
            cap_add = list(cap_add)
        self.cap_add = cap_add
        if cap_drop is not None:
            cap_drop = list(cap_drop)
        self.cap_drop = cap_drop
        if restart_policy is not None:
            if isinstance(restart_policy, str):
                restart_policy = RestartPolicy(restart_policy)
        self.restart_policy = restart_policy
        self.network_mode = network_mode
        if devices is not None:
            devices = list(devices)
            for index, dev in enumerate(devices):
                if isinstance(dev, str):
                    devices[index] = DeviceToAdd(dev)
        self.devices = devices
        if ulimits is not None:
            ulimits = list(ulimits)
        self.ulimits = ulimits
        if security_opt is not None:
            security_opt = list(security_opt)
        self.security_opt = security_opt
        self.log_config = log_config
        self.cgroup_parent = cgroup_parent
        self.volume_driver = volume_driver
        self.shm_size = shm_size

    @property
    def oom_kill_disable(self):
        if self.oom_kill is None:
            return None
        return not self.oom_kill

    @property
    def memory_swap(self):
        if self.swap is None:
            return None
        if self.swap < 0:
            return -1
        else:
            return self.memory + self.swap

    @property
    def port_bindings_json(self):
        if self.port_bindings is None:
            return None
        bindings = {}
        for binding in self.port_bindings:
            bindings.update(binding.json())
        return bindings

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
        ('PortBindings', (1, 14), 'port_bindings_json'),
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
        ('ShmSize', (1, 22), 'shm_size'),
    )

    def json(self, api_version: Tuple[int, int]=(1, 14)):
        return json_update({}, self, self.JSON_FIELDS, api_version)
