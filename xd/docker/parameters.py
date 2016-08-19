"""Module containing helper classes and functions for handling Docker Remote
API parameters."""

import collections
import re

from typing import Any, Optional, Union, Mapping, Sequence, Tuple, Dict, List
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
           'Hostname', 'Domainname', 'MacAddress', 'Username',
           'Repository', 'RepoTags', 'ContainerName',
           'Env', 'Port', 'PortBinding', 'VolumeMount', 'VolumeBinding',
           'ContainerLink', 'Cpuset',
           'HostnameIPMapping', 'VolumesFrom', 'RestartPolicy',
           'DeviceToAdd', 'Ulimit', 'LogConfiguration',
           'AuthConfig', 'CredentialAuthConfig', 'TokenAuthConfig',
           'RegistryAuthConfig',
           'ContainerConfig', 'HostConfig']


def json_update(obj: Dict[str, Any], values: Dict[str, Any],
                json_fields: Sequence[Tuple[str, Tuple[int, int], str]],
                api_version: Optional[ApiVersion]=None):
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
    for json_name, value_name, version_limit in json_fields:
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
        if version_limit is not None:
            min_version, max_version = version_limit
            if api_version and (
                    (min_version and api_version < min_version) or
                    (max_version and api_version > max_version)):
                raise ValueError('%s not supported by Remote API %s' % (
                    json_name, '.'.join([str(i) for i in api_version])))
        obj[json_name] = value
    return obj


class Parameter(object):
    """Base class for all XD Docker parameter classes."""

    def __str__(self):
        return str(self.json())

    def json(self, api_version: Optional[ApiVersion]=None):
        """Return Docker Remote API JSON representation.

        Arguments:
          api_version: Docker Remote API version.
        """
        raise NotImplementedError


class Hostname(Parameter):
    """Hostname.

    A Hostname instance represents a network hostname.  A hostname must not
    contain dots ('.').  To specify a fully qualified domain name, use
    :class:`.Domainname`.

    Arguments:
      hostname: Hostname.

    Attributes:
      hostname (str): Hostname.
    """

    HOSTNAME_RE = re.compile(r'[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$')

    def __init__(self, hostname: str):
        if not self.HOSTNAME_RE.match(hostname):
            raise ValueError('invalid hostname: %s' % hostname)
        self.hostname = hostname

    def json(self, api_version: Optional[ApiVersion]=None):
        return self.hostname


class Domainname(Hostname):
    """Domain name.

    A Domainname instance represents a network domain name.

    Arguments:
      domainname: Domain name.

    Attributes:
      domainname (str): Domain name.
    """

    DOMAINNAME_RE = re.compile(r'%s(?:\.%s)*$' % (
        Hostname.HOSTNAME_RE.pattern[:-1], Hostname.HOSTNAME_RE.pattern[:-1]))

    def __init__(self, domainname: str):
        if not self.DOMAINNAME_RE.match(domainname):
            raise ValueError('invalid domainname: %s' % domainname)
        self.domainname = domainname

    def json(self, api_version: Optional[ApiVersion]=None):
        return self.domainname


class MacAddress(Parameter):
    """Ethernet MAC address.

    A MacAddress instance represents an Ethernet MAC address.

    Arguments:
      addr: MAC address (fx. '01:02:03:04:05:06').

    Attributes:
      addr (str): MAC address (fx. '01:02:03:04:05:06').
    """

    MACADDRESS_RE = re.compile('[0-9a-fA-F]{2}(:[0-9a-fA-F]{2}){5}$')

    def __init__(self, addr: str):
        if not self.MACADDRESS_RE.match(addr):
            raise ValueError('invalid MAC address: %s' % addr)
        self.addr = addr

    def json(self, api_version: Optional[ApiVersion]=None):
        return self.addr


class Username(Parameter):
    """User name.

    A Username instance represents a UNIX user name.

    Arguments:
      username: User name.

    Attributes:
      username (str): User name.
    """

    USERNAME_RE = re.compile(r'[a-z0-9][a-z0-9_-]*$')

    def __init__(self, username: str):
        if not self.USERNAME_RE.match(username):
            raise ValueError('invalid username: %s' % username)
        self.username = username

    def json(self, api_version: Optional[ApiVersion]=None):
        return self.username


class Repository(Parameter):
    """Repository name (and optionally tag) parameter.

    A Repository instance is used to represent a Docker repository name, or
    repository name and tag.

    Arguments:
      repo: Repository name, or name and tag (separated by ':').

    Attributes:
      name (str): Repository name.
      tag (Optional[str]): Repository tag.
    """
    NAME_RE = re.compile(
        r'(?:(?:%s:\d+/)?|/)?' % (Domainname.DOMAINNAME_RE.pattern[:-1]) +
        r'[a-z0-9-_\.]+(?:(?:/[a-z0-9-_\.]+)+)?$')
    TAG_RE = re.compile(r'[a-zA-Z0-9-_.]+$')
    NAME_AND_TAG_RE = re.compile(r'(%s):(%s)?$' % (
        NAME_RE.pattern[:-1], TAG_RE.pattern[:-1]))

    def __init__(self, repo: str):
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

    def json(self, api_version: Optional[ApiVersion]=None):
        if self.tag:
            return "%s:%s" % (self.name, self.tag)
        else:
            return self.name


class RepoTags(Parameter):
    """List of repository name and tags.

    A RepoTags instance is used to represent a list of repository name and
    tags.

    Arguments:
      repos: List of repository name and tags (separated by ':').

    Attributes:
      repos (List[Repository]): List of repository name and tags.
    """

    def __init__(self, repos: List[str]):
        self.repos = [Repository(repo) for repo in repos]

    def json(self, api_version: Optional[ApiVersion]=None):
        return [str(repo) for repo in self.repos]


class ContainerName(Parameter):
    """Container name parameter.

    A ContainerName instance is used to represent a Docker container name.

    Arguments:
      name: Container name

    Attributes:
      name (str): Container name.
    """

    NAME_RE = re.compile(r'/?[a-zA-Z0-9_-]+$')

    def __init__(self, name: str):
        if self.NAME_RE.match(name):
            self.name = name
            return
        raise ValueError('invalid container name: %s' % name)

    def json(self, api_version: Optional[ApiVersion]=None):
        return self.name


class Env(Parameter):
    """Environment variables.

    An Environment instance contains the environment variables for a Docker
    container.

    Arguments:
      env: Environment variables, name/value pairs.

    Attributes:
      env (Mapping[str, str]): Environment variables, name/value pairs.
    """

    KEY_RE = re.compile(r'[a-zA-Z_][a-zA-Z0-9_]*$')

    def __init__(self, env: Optional[Mapping[str, str]]=None):
        self.env = env
        if env:
            for k in env:
                if not isinstance(k, str):
                    raise TypeError('Env variable name must be string: %s'
                                    % type(k))
                if not self.KEY_RE.match(k):
                    raise ValueError('Invalid Env variable name: %s' % k)

    def json(self, api_version: Optional[ApiVersion]=None):
        if self.env is None:
            return None
        else:
            return ['%s=%s' % (k, v) for k, v in self.env.items()]


def validate_network_port(port: int, protocol: str):
    if port <= 0 or port > 65535:
        raise ValueError('port must be > 0 and <= 65535')
    if protocol not in ('tcp', 'udp'):
        raise ValueError("protocol must be either 'tcp' or 'udp'")


class Port(Parameter):
    """Network port.

    A Port instance represents a network port (TCP or UDP).

    Arguments:
      port: Port number.
      protocol: Protocol ('tcp' or 'udp').

    Attributes:
      port (int): Port number.
      protocol (str): Protocol ('tcp' or 'udp').
    """

    def __init__(self, port: int, protocol: str='tcp'):
        validate_network_port(port, protocol)
        self.port = port
        self.protocol = protocol

    def json(self, api_version: Optional[ApiVersion]=None):
        return '%d/%s' % (self.port, self.protocol)


class PortBinding(Parameter):
    """Docker container port binding.

    A PortBinding instance represents a binding of a network port of a Docker
    container to a host port.

    Arguments:
      port: Container port number.
      protocol: Protocol ('tcp' or 'udp').
      host_ip: Host IP address.
      host_port: Host port number (defaults to container port number).

    Attributes:
      port (int): Container port number (1 ... 65535).
      protocol (str): Protocol ('tcp' or 'udp').
      host_ip (Optional[IPAddress]): Host IP address.
      host_port (int): Host port number (1 ... 65535).
    """

    def __init__(self, port: int, protocol: str='tcp',
                 host_ip: Optional[IPAddress]=None,
                 host_port: Optional[int]=None):
        validate_network_port(port, protocol)
        self.port = port
        self.protocol = protocol
        self.host_ip = host_ip
        if host_port is None:
            host_port = port
        elif host_port <= 0 or host_port > 65535:
            raise ValueError('host_port must be > 0 and <= 65535')
        self.host_port = host_port

    def json(self, api_version: Optional[ApiVersion]=None):
        host_binding = {'HostPort': str(self.host_port)}
        if self.host_ip is not None:
            host_binding['HostIp'] = str(self.host_ip)
        return {'%d/%s' % (self.port, self.protocol): [host_binding]}


class VolumeMount(Parameter):
    """Volume mount point.

    A VolumeMount instance represents a container mount point.

    Arguments:
      source: Host path.
      destination: Container path.
      ro: Read-only mount.
      label_mode: SELinux label mode ('z' or 'Z').

    Attributes:
      source (str): Source path.
      destination (str): Destination path.
      ro (bool): Read-only mount.
      label_mode (str): SELinux label mode ('', 'z', or 'Z').
    """

    def __init__(self, source: str, destination: str, ro: bool=False,
                 label_mode: Optional[str]=None):
        self.source = source
        self.destination = destination
        self.ro = ro
        self.label_mode = label_mode or ''

    def json(self, api_version: Optional[ApiVersion]=None):
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

    Arguments:
      container_path: Container path to bind the volume to.
      volume: Host path or volume name, identifying the volume
        to bind to.  Host path must start with a '/'.  Volume name must
        not begin with a '/'.
      ro: Read-only mount.

    Attributes:
      container_path (str): Container path to bind the volume to.
      volume (Optional[str]): Host path or volume name, identifying the volume
        to bind to.
      ro (bool): Read-only mount.
    """

    def __init__(self, container_path: str, volume: Optional[str]=None,
                 ro: bool=False):
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

    def json(self, api_version: Optional[ApiVersion]=None):
        if not self.volume:
            return self.container_path
        if self.ro:
            return '%s:%s:ro' % (self.volume, self.container_path)
        else:
            return '%s:%s' % (self.volume, self.container_path)


class ContainerLink(Parameter):
    """Container link.

    A ContainerLink instance represents a link to another container.

    Arguments:
      name: Name of container to link to.
      alias: Alias to use for linked container.

    Attributes:
      name (str): Name of container to link to.
      alias (str): Alias to use for linked container.
    """

    def __init__(self, name: str, alias: str):
        self.name = name
        self.alias = alias

    def json(self, api_version: Optional[ApiVersion]=None):
        return '%s:%s' % (self.name, self.alias)


class Cpuset(Parameter):
    """List of CPUs.

    A Cpuset instance represents a set of CPU or memory nodes, for use when
    specifying where to run a container.

    Arguments:
      cpuset: Cpuset specification.  See `cpuset(7)`_ for syntax.

    Attributes:
      cpuset (str): Cpuset specification.

    .. _cpuset(7): http://man7.org/linux/man-pages/man7/cpuset.7.html
    """

    CPUSET_LIST_RE = re.compile(r'(\d|[1-9]\d+)([,-](\d|[1-9]\d+))*$')

    def __init__(self, cpuset: str):
        if not self.CPUSET_LIST_RE.match(cpuset):
            raise ValueError('invalid cpuset: %s' % cpuset)
        self.cpuset = cpuset

    def json(self, api_version: Optional[ApiVersion]=None):
        return self.cpuset


class HostnameIPMapping(Parameter):
    """Hostname to IP address mapping.

    A HostnameIPMapping instance represents a mapping from a hostname to an IP
    address (IPv6 or IPv4).

    Arguments:
      hostname: Hostname.
      ip: IP address.

    Attributes:
      hostname (Hostname): Hostname.
      ip (IPAddress): IP address.
    """

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

    def json(self, api_version: Optional[ApiVersion]=None):
        return '%s:%s' % (self.hostname.json(api_version), self.ip)


class VolumesFrom(Parameter):
    """Docker container to inherit volumes from.

    A VolumesFrom instance represents a single docker container to inherit
    volumes from.

    Arguments:
      name: Container name.
      ro: Mount volumes read-only (default is read/write).

    Attributes:
      name (ContainerName): Container name.
      ro (Optional[bool]): Mount volumes read-only.
    """

    def __init__(self, name: Union[ContainerName, str],
                 ro: Optional[bool]=None):
        if isinstance(name, str):
            name = ContainerName(name)
        self.name = name
        self.ro = ro

    def json(self, api_version: Optional[ApiVersion]=None):
        if self.ro is None:
            return self.name.json(api_version)
        else:
            return '%s:%s' % (self.name.json(api_version),
                              'ro' if self.ro else 'rw')


class RestartPolicy(Parameter):
    """Restart policy for when the container exits.

    A RestartPolicy instance represents the restart policy to use when
    container exits.

    Arguments:
      policy: One of 'always', 'unless-stopped', or 'on-failure.
      maximum_retry_count: Number of times to retry before giving up
        (required and only allowed together with 'on-failure')

    Attributes:
      policy (str): One of 'always', 'unless-stopped', or 'on-failure'.
      maximum_retry_count (int): Number of times to retry before giving up
        (only present when policy is 'on-failure').
    """

    def __init__(self, policy: str, maximum_retry_count: Optional[int]=None):
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

    def json(self, api_version: Optional[ApiVersion]=None):
        d = {'Name': self.policy}
        if self.policy == 'on-failure':
            d['MaximumRetryCount'] = self.maximum_retry_count
        return d


class DeviceToAdd(Parameter):
    """Device to add to container.

    A DeviceToAdd instance represents a device to add to a container.

    Arguments:
      path_on_host: Device path on host.
      path_in_container: Device path in container (defaults to
        path_on_host).
      cgroup_permissions: Access permission, composition of 'r' (read),
        'w' (write), and 'm' (mknod) (defaults to 'rwm').

    Attributes:
      path_on_host (str): Device path on host.
      path_in_container (str): Device path in container.
      cgroup_permissions (str): Access permission, composition of 'r' (read),
        'w' (write), and 'm' (mknod).
    """

    def __init__(self, path_on_host: str,
                 path_in_container: Optional[str]=None,
                 cgroup_permissions: str='rwm'):
        self.path_on_host = path_on_host
        if path_in_container is None:
            path_in_container = path_on_host
        self.path_in_container = path_in_container
        self.cgroup_permissions = cgroup_permissions

    def json(self, api_version: Optional[ApiVersion]=None):
        return {'PathOnHost': self.path_on_host,
                'PathInContainer': self.path_in_container,
                'CgroupPermissions': self.cgroup_permissions}


class Ulimit(Parameter):
    """Ulimit parameter.

    A Ulimit instance represents a ulimit (user limit) to set in a container.

    Arguments:
      name: Name of ulimit.
      soft: Soft limit.
      hard: Hard limit (defaults to soft limit).

    Attributes:
      name (str): Name of ulimit.
      soft (str): Soft limit.
      hard (str): Hard limit.
    """

    def __init__(self, name: str, soft: int, hard: Optional[int]=None):
        self.name = name
        self.soft = soft
        if hard is None:
            hard = soft
        self.hard = hard

    def json(self, api_version: Optional[ApiVersion]=None):
        return {'Name': self.name,
                'Soft': self.soft,
                'Hard': self.hard}


class LogConfiguration(Parameter):
    """Log configuration for container.

    A LogConfiguration instance represents configuration of how logging is
    done for a container.

    Arguments:
      type: Logging driver name.
      config: Driver specific configuration parameters.

    Attributes:
      type (str): Logging driver name.
      config (Dict[str, str]): Driver specific configuration parameters.
    """

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

    def json(self, api_version: Optional[ApiVersion]=None):
        return {'Type': self.type, 'Config': self.config}


class AuthConfig(Parameter):
    """Login information for a docker registry.

    An AuthConfig instance represents login information for authenticating to
    a docker repository.
    """


class CredentialAuthConfig(AuthConfig):
    """Credential based login information for a docker registry.

    A CredentialAuthConfig instance represents credential based login
    information for authenticating to a docker repository.

    Arguments:
      username: User name.
      password: Password.
      email: Email address.

    Attributes:
      username (str): User name.
      password (str): Password.
      email (Optional[str]): Email address.
    """

    def __init__(self, username: str, password: str,
                 email: Optional[str]=None):
        self.username = username
        self.password = password
        self.email = email

    def json(self, api_version: Optional[Tuple[int, int]]=None):
        obj = {'username': self.username,
               'password': self.password}
        if self.email:
            obj['email'] = self.email
        return obj


class TokenAuthConfig(AuthConfig):
    """Token based login information for a docker registry.

    A TokenAuthConfig instance represents token based login information for
    authenticating to a docker repository.

    Arguments:
      token: Login token.

    Attributes:
      token (str): Login token.
    """

    def __init__(self, token: str):
        self.token = token

    def json(self, api_version: Optional[Tuple[int, int]]=None):
        return {'registrytoken': self.token}


class RegistryAuthConfig(Parameter):
    """Docker registry authentication configuration.

    A RegistryAuthConfig instance represents the login information for one or
    more docker registries.

    Arguments:
      registry_auths: Mapping of registry hostnames to the login
        information for authenticating to that registry. Only the registry
        domain name (and port if not the default "443") are
        required. However (for legacy reasons) the "official" Docker,
        Inc. hosted registry must be specified with both a "https://"
        prefix and a "/v1/" suffix even though Docker will prefer to use
        the v2 registry API.

    Attributes:
      registry_auths: Mapping of registry hostnames to login information.
    """

    def __init__(self, registry_auths: Mapping[str, AuthConfig]):
        self.registry_auths = dict(registry_auths)

    def json(self, api_version: Optional[Tuple[int, int]]=None):
        obj = {}
        for hostname, auth_config in self.registry_auths.items():
            obj[hostname] = auth_config.json(api_version)
        return obj


class ContainerConfig(Parameter):
    """Container configuration parameter.

    A ContainerConfig instance represents the configuration of a container.

    Arguments:
      image: Image to create container from.
      command: Command to run.
      entrypoint: Container entrypoint.
      on_build: Trigger instructions to be executed later (when used as base
        image for another build).
      hostname: Hostname to use for the container.
      domainname: Domain name to use for the container.
      user: User inside the container.
      attach_stdin: Attach to stdin.
      attach_stdout: Attach to stdout.
      attach_stderr: Attach to stderr.
      tty: Attach standard streams to a tty.
      open_stdin: Open stdin.
      stdin_once: Close stdin after the client disconnects.
      env: Environment variables.
      labels: Labels to set on container.
      working_dir: Working directory for command to run in.
      network: Whether to enable networking in the container.
      mac_address: MAC address.
      exposed_ports: Exposed ports.
      volumes: List of (in container) paths to use as volumes.
      stop_signal: Signal to stop container.

    Attributes:
      image (str): Image to create container from.
      command (Optional[Command]): Command to run.
      entrypoint (Optional[Command]): Container entrypoint.
      on_build (Optional[Sequence[str]]): Trigger instructions to be executed
        later (when used as base image for another build).
      hostname (Optional[Hostname]): Hostname to use for the container.
      domainname (Optional[Domainname]): Domain name to use for the container.
      user (Optional[Username]): User inside the container.
      attach_stdin (Optional[bool]): Attach to stdin.
      attach_stdout (Optional[bool]): Attach to stdout.
      attach_stderr (Optional[bool]): Attach to stderr.
      tty (Optional[bool]): Attach standard streams to a tty.
      open_stdin (Optional[bool]): Open stdin.
      stdin_once (Optional[bool]): Close stdin after the client disconnects.
      env (Optional[Env]): Environment variables.
      labels (Optional[Mapping[str, str]]): Labels to set on container.
      working_dir (Optional[str]): Working directory for command to run in.
      network (Optional[bool]): Whether to enable networking in the container.
      mac_address (Optional[MacAddress]): MAC address.
      exposed_ports (Optional[Sequence[Port]]): Exposed ports.
      volumes (Optional[Sequence[str])): List of (in container) paths to use
        as volumes.
      stop_signal (Optional[Union[int, str]]): Signal to stop container.
    """

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
                 network: Optional[bool]=None,
                 mac_address: Optional[Union[MacAddress, str]]=None,
                 exposed_ports: Optional[Sequence[Port]]=None,
                 volumes: Optional[Sequence[str]]=None,
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
            domainname = Domainname(domainname)
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
    def _network_disabled(self):
        if self.network is None:
            return None
        return not self.network

    @property
    def _volumes_map(self):
        if self.volumes is None:
            return None
        return {volume: {} for volume in self.volumes}

    JSON_FIELDS = (
        ('Image', 'image', None),
        ('Cmd', 'command', None),
        ('Entrypoint', 'entrypoint', ((1, 15), None)),
        ('OnBuild', 'on_build', ((1, 16), None)),
        ('Hostname', 'hostname', None),
        ('Domainname', 'domainname', None),
        ('User', 'user', None),
        ('AttachStdin', 'attach_stdin', None),
        ('AttachStdout', 'attach_stdout', None),
        ('AttachStderr', 'attach_stderr', None),
        ('Tty', 'tty', None),
        ('OpenStdin', 'open_stdin', None),
        ('StdinOnce', 'stdin_once', None),
        ('Env', 'env', None),
        ('Labels', 'labels', ((1, 18), None)),
        ('WorkingDir', 'working_dir', None),
        ('NetworkDisabled', '_network_disabled', None),
        ('MacAddress', 'mac_address', ((1, 15), None)),
        ('ExposedPorts', 'exposed_ports', None),
        ('Volumes', '_volumes_map', None),
        ('StopSignal', 'stop_signal', ((1, 21), None)),
    )

    def json(self, api_version: Tuple[int, int]=(1, 14)):
        return json_update({}, self, self.JSON_FIELDS, api_version)


class HostConfig(Parameter):
    """Docker container host configuration.

    Arguments:
      binds: List of volume bindings.
      links: List of links to other containers.
      lxc_config: LXC specific configurations. Only valid when using the lxc
        execution driver.
      port_bindings: List of port bindings, ie. container ports that exposed
        as host ports.
      publish_all_ports: Allocate a random host port for all exposed ports.
      privileged: Container has full access to host.
      read_only_rootfs: Mount container root filesystem read only.
      dns: List of DNS servers to use.
      dns_options: List of DNS options.
      dns_search: List of DNS search domains.
      extra_hosts: A list of hostname to IP mappings to add to container's
        /etc/hosts file.
      volumes_from: List of containers to inherit volumes from.
      cap_add: List of kernel capabilities to add to container.
      cap_drop: List of kernel capabilities to drop from container.
      group_add: List of additional groups that the container process will
        run as.
      restart_policy: Behavior when container exits.
      network_mode: Networking mode for the container.
      devices: List of devices to add to container.
      ulimits: List of ulimits to set in container.
      security_opt: List of string values to customize labels for MLS systems,
        such as SELinux.
      log_config: Log configuration for container.
      cgroup_parent: Path to cgroups under which the container's cgroup is
        created.
      volume_driver: Driver that this container uses to mount volumes.
      shm_size: Size of /dev/shm in bytes.
      memory: Memory limit in bytes.
      swap: Swap limit in bytes.
      memory_reservation: Memory soft limit in bytes.
      kernel_memory: Kernel memory limit in bytes.
      cpu_shares: CPU shares relative to other containers.
      cpu_period: Length of a CPU period in microseconds.
      cpu_quota: Microseconds of CPU time that the container can get in a
        CPU period.
      cpuset_cpus: Cgroups cpuset.cpu to use.
      cpuset_mems: Cgroups cpuset.mem to use.
      blkio_weight: Relative block io weight (10 ... 1000).
      memory_swappiness: Memory swappiness behavior (10 ... 100).
      oom_kill: Enable OOM killer for container.

    Attributes:
      binds (Optional[List[VolumeBinding]]): List of volume bindings.
      links (Optional[List[ContainerLink]]): List of links to other containers.
      lxc_config (Optional[Dict[str, str]]): LXC specific configurations. Only
        valid when using the lxc execution driver.
      port_bindings (Optional[List[PortBinding]]): List of port bindings, ie.
        container ports that exposed as host ports.
      publish_all_ports (Optional[bool]): Allocate a random host port for all
        exposed ports.
      privileged (Optional[bool]): Container has full access to host.
      read_only_rootfs (Optional[bool]): Mount container root filesystem read
        only.
      dns (Optional[List[IPAddress]]): List of DNS servers to use.
      dns_options (Optional[List[str]]): List of DNS options.
      dns_search (Optional[List[str]]): List of DNS search domains.
      extra_hosts (Optional[List[HostnameIPMapping]]): A list of hostname to
        IP mappings to add to container's /etc/hosts file.
      volumes_from (Optional[List[VolumesFrom]]): List of containers to
        inherit volumes from.
      cap_add (Optional[List[str]]): List of kernel capabilities to add to
        container.
      cap_drop (Optional[List[str]]): List of kernel capabilities to drop
        from container.
      group_add (Optional[List[str]]): List of additional groups that the
        container process will run as.
      restart_policy (Optional[RestartPolicy]): Behavior when container exits.
      network_mode (Optional[str]): Networking mode for the container.
      devices (Optional[List[DeviceToAdd]]): List of devices to add to
        container.
      ulimits (Optional[List[Ulimit]]): List of ulimits to set in container.
      security_opt (Optional[List[str]]): List of string values to customize
        labels for MLS systems, such as SELinux.
      log_config (Optional[LogConfiguration]): Log configuration for container.
      cgroup_parent (Optional[str]): Path to cgroups under which the
        container's cgroup is created.
      volume_driver (Optional[str]): Driver that this container uses to mount
        volumes.
      shm_size (Optional[int]): Size of /dev/shm in bytes.
      memory (Optional[int]): Memory limit in bytes.
      swap (Optional[int]): Swap limit in bytes.
      memory_reservation (Optional[int]): Memory soft limit in bytes.
      kernel_memory (Optional[int]): Kernel memory limit in bytes.
      cpu_shares (Optional[int]): CPU shares relative to other containers.
      cpu_period (Optional[int]): Length of a CPU period in microseconds.
      cpu_quota (Optional[int]): Microseconds of CPU time that the container
        can get in a CPU period.
      cpuset_cpus (Optional[Cpuset]): Cgroups cpuset.cpu to use.
      cpuset_mems (Optional[Cpuset]): Cgroups cpuset.mem to use.
      blkio_weight (Optional[int]): Relative block io weight (10 ... 1000).
      memory_swappiness (Optional[int]): Memory swappiness behavior
        (10 ... 100).
      oom_kill (Optional[bool]): Enable OOM killer for container.
    """

    def __init__(self,
                 binds: Optional[Sequence[VolumeBinding]]=None,
                 links: Optional[Sequence[ContainerLink]]=None,
                 lxc_conf: Optional[Mapping[str, str]]=None,
                 port_bindings: Optional[Sequence[PortBinding]]=None,
                 publish_all_ports: Optional[bool]=None,
                 privileged: Optional[bool]=None,
                 read_only_rootfs: Optional[bool]=None,
                 dns: Optional[Sequence[IPAddress]]=None,
                 dns_options: Optional[Sequence[str]]=None,
                 dns_search: Optional[Sequence[str]]=None,
                 extra_hosts: Optional[Sequence[
                     Union[HostnameIPMapping, str]]]=None,
                 volumes_from: Optional[Sequence[
                     Union[VolumesFrom, str]]]=None,
                 cap_add: Optional[Sequence[str]]=None,
                 cap_drop: Optional[Sequence[str]]=None,
                 group_add: Optional[Sequence[str]]=None,
                 restart_policy: Optional[RestartPolicy]=None,
                 network_mode: Optional[str]=None,
                 devices: Optional[Sequence[
                     Union[DeviceToAdd, str]]]=None,
                 ulimits: Optional[Sequence[Ulimit]]=None,
                 security_opt: Optional[Sequence[str]]=None,
                 log_config: Optional[LogConfiguration]=None,
                 cgroup_parent: Optional[str]=None,
                 volume_driver: Optional[str]=None,
                 shm_size: Optional[int]=None,
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
                 oom_kill: Optional[bool]=None):
        if binds is not None:
            binds = list(binds)
        self.binds = binds
        if links is not None:
            links = list(links)
        self.links = links
        if lxc_conf is not None:
            lxc_conf = dict(lxc_conf)
        self.lxc_conf = lxc_conf
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
        if group_add is not None:
            group_add = list(group_add)
        self.group_add = group_add
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

    @property
    def _oom_kill_disable(self):
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
    def _port_bindings_json(self):
        if self.port_bindings is None:
            return None
        bindings = {}
        for binding in self.port_bindings:
            bindings.update(binding.json())
        return bindings

    JSON_FIELDS = (
        ('Binds', 'binds', None),
        ('Links', 'links', None),
        ('LxcConf', 'lxc_conf', None),
        ('Memory', 'memory', ((1, 18), None)),
        ('MemorySwap', 'memory_swap', ((1, 18), None)),
        ('MemoryReservation', 'memory_reservation', ((1, 21), None)),
        ('KernelMemory', 'kernel_memory', ((1, 21), None)),
        ('CpuShares', 'cpu_shares', ((1, 18), None)),
        ('CpuPeriod', 'cpu_period', ((1, 19), None)),
        ('CpuQuota', 'cpu_quota', ((1, 19), None)),
        ('CpusetCpus', 'cpuset_cpus', ((1, 18), None)),
        ('CpusetMems', 'cpuset_mems', ((1, 19), None)),
        ('BlkioWeight', 'blkio_weight', ((1, 19), None)),
        ('MemorySwappiness', 'memory_swappiness', ((1, 20), None)),
        ('OomKillDisable', '_oom_kill_disable', ((1, 19), None)),
        ('PortBindings', '_port_bindings_json', None),
        ('PublishAllPorts', 'publish_all_ports', None),
        ('Privileged', 'privileged', None),
        ('ReadonlyRootfs', 'read_only_rootfs', ((1, 17), None)),
        ('Dns', 'dns', None),
        ('DnsOptions', 'dns_options', ((1, 21), None)),
        ('DnsSearch', 'dns_search', ((1, 15), None)),
        ('ExtraHosts', 'extra_hosts', ((1, 15), None)),
        ('GroupAdd', 'group_add', ((1, 20), None)),
        ('VolumesFrom', 'volumes_from', None),
        ('CapAdd', 'cap_add', None),
        ('CapDrop', 'cap_drop', None),
        ('RestartPolicy', 'restart_policy', ((1, 15), None)),
        ('NetworkMode', 'network_mode', ((1, 15), None)),
        ('Devices', 'devices', ((1, 15), None)),
        ('Ulimits', 'ulimits', ((1, 18), None)),
        ('LogConfig', 'log_config', ((1, 18), None)),
        ('SecurityOpt', 'security_opt', ((1, 17), None)),
        ('CgroupParent', 'cgroup_parent', ((1, 18), None)),
        ('VolumeDriver', 'volume_driver', ((1, 21), None)),
        ('ShmSize', 'shm_size', ((1, 22), None)),
    )

    def json(self, api_version: Tuple[int, int]=(1, 14)):
        return json_update({}, self, self.JSON_FIELDS, api_version)
