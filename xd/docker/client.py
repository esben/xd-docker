"""Module containing DockerClient and associated exceptions."""


import urllib.parse
import requests
import requests_unixsocket
import json
import base64
import os
import io
import tarfile
import re
import functools

from typing import Optional, Union, Sequence, Dict, Tuple, List

from xd.docker.container import Container
from xd.docker.image import Image
from xd.docker.parameters import ContainerConfig, HostConfig, ContainerName, \
    Repository, RegistryAuthConfig, VolumeMount, json_update

import logging
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

requests_unixsocket.monkeypatch()


__all__ = ['DockerClient', 'HTTPError', 'ClientError', 'ServerError']


class HTTPError(Exception):
    def __init__(self, url, code):
        self.url = url
        self.code = code


class ClientError(HTTPError):
    def __init__(self, url, code):
        super(ClientError, self).__init__(url, code)


class ServerError(HTTPError):
    def __init__(self, url, code):
        super(ServerError, self).__init__(url, code)


class DockerClient(object):
    """Docker client.

    A DockerClient instance is used to communicate with Docker daemon (or
    something else that is speaking Docker Remote API).

    Arguments:
      host: URL to Docker daemon socket to connect to.

    :Example:

    Connect to docker daemon on localhost TCP socket:

    >>> docker = DockerClient('tcp://127.0.0.1:2375')

    Connect to docker daemon on UNIX domain socket:

    >>> docker = DockerClient('unix:///var/run/docker.sock')
    """

    def __init__(self, host: str = 'unix:///var/run/docker.sock'):
        if host.startswith('unix://'):
            host = 'http+unix://' + urllib.parse.quote_plus(host[7:])
        elif host.startswith('tcp://'):
            host = 'http://' + host[6:]
        else:
            raise ValueError('Invalid host value: {}'.format(host))
        self.base_url = host

    @staticmethod
    def _check_http_status_code(url, status_code):
        if status_code >= 200 and status_code < 300:
            return
        elif status_code >= 400 and status_code <= 499:
            raise ClientError(url, status_code)
        elif status_code >= 500 and status_code <= 599:
            raise ServerError(url, status_code)
        else:
            raise HTTPError(url, status_code)

    @staticmethod
    def _process_response_output(r, output, last_line=False):
        decoder = json.JSONDecoder()
        failed = False
        for line in r.iter_lines():
            line = line.decode('utf-8')
            index = 0
            while index < len(line):
                data, extra_data_index = decoder.raw_decode(line[index:])
                index += extra_data_index
                for t in ('progressDetail', 'stream', 'status', 'error'):
                    if t not in data:
                        continue
                    if t not in output:
                        break
                    print(data[t].rstrip('\n'))
                if 'error' in data:
                    failed = True
        if failed:
            return False
        else:
            if last_line:
                return data
            else:
                return True

    def _get(self, url, params=None, headers=None, stream=False):
        url = self.base_url + url
        r = requests.get(url, params=params, headers=headers, stream=stream)
        self._check_http_status_code(url, r.status_code)
        return r

    def _post(self, url, params=None, headers=None, data=None, stream=False):
        url = self.base_url + url
        r = requests.post(url, params=params, headers=headers, data=data,
                          stream=stream)
        self._check_http_status_code(url, r.status_code)
        return r

    def _delete(self, url, params=None, stream=False):
        url = self.base_url + url
        r = requests.delete(url, params=params, stream=stream)
        self._check_http_status_code(url, r.status_code)
        return r

    def version(self) -> Tuple[int, int]:
        """Get Docker Remote API version.

        Raises:
          ServerError: Server error.

        Returns:
          Major/minor version number of Docker daemon (Docker Remote API).
        """
        r = self._get('/version')
        version = json.loads(r.text)
        return version

    @property
    @functools.lru_cache(maxsize=1)
    def api_version(self):
        version = self.version()
        return tuple([int(i) for i in version['ApiVersion'].split('.')])

    def ping(self) -> None:
        """Ping the docker server.

        Raises:
          ServerError: Server error.
        """
        self._get('/_ping')

    def containers(self, only_running: bool = True) -> List[Container]:
        """Get list of containers.

        By default, only running containers are returned.

        Keyword arguments:
          only_running: List only running containers (if True), or all
            containers (if False).

        Raises:
          ClientError: Bad parameter.
          ServerError: Server error.

        Returns:
          List of containers.
        """
        params = {}
        params['all'] = not only_running
        r = self._get('/containers/json', params=params)
        containers = json.loads(r.text)
        return [Container(self, list_response=c) for c in containers]

    def images(self) -> List[Image]:
        """Get list of images.

        Raises:
          ServerError: Server error.

        Returns:
          List of images.
        """
        response = self._get('/images/json')
        images = json.loads(response.text)
        return [Image(self, list_response=image) for image in images]

    def image_inspect(self, name, raw=False):
        """Get image with low-level information.

        Get low-level information of a named image.  Returns Image
        instance with the information.

        Arguments:
        name -- name of image.

        Keyword arguments:
        raw -- if True, return the low-level image information in raw format
               instaed of Image instance.
        """
        r = self._get('/images/{}/json'.format(name))
        i = json.loads(r.text)
        if raw:
            return i
        else:
            return Image(
                self, id_=i['Id'], created=i['Created'], size=i['Size'],
                parent=i['Parent'])

    def image_build(self, context: str,
                    output=('error', 'stream', 'status'),
                    dockerfile: Optional[str]=None,
                    tag: Optional[Union[Repository, str]]=None,
                    cache: bool=True,
                    pull: Optional[bool]=None,
                    rm: Optional[bool]=None,
                    force_rm: Optional[bool]=None,
                    host_config: Optional[HostConfig]=None,
                    registry_config: Optional[RegistryAuthConfig]=None,
                    buildargs: Optional[Dict[str, str]]=None):
        """Build image.

        Build image from a given context or stand-alone Dockerfile.

        Arguments:
        context -- path to directory containing build context, or path to a
                   stand-alone Dockerfile.

        Keyword arguments:
        output -- tuple/list of with type of output information to allow
                  (Default: ('stream', 'status', 'error')).
        dockerfile -- path to dockerfile in build context.
        tag -- repository name and tag to be applied to the resulting image.
        cache -- use the cache when building the image (default: True).
        pull -- attempt to pull the image even if an older image exists locally
                (default: False).
        rm -- False/True. Remove intermediate containers after a
              successful build (default: True).
        force_rm -- False/True. Always remove intermediate containers after
                    build (default: False).
        host_config -- HostConfig instance.
        registry_config -- RegistryAuthConfig instance.
        buildargs -- build-time environment variables.
        """

        # Handle convenience argument types
        if isinstance(tag, str):
            tag = Repository(tag)

        # TODO: take from HostConfig:
        # memory
        # swap
        # cpu_shares
        # cpu_period
        # cpuset_cpus

        # Request headers
        headers = {'content-type': 'application/tar'}
        if registry_config:
            registry_config = json.dumps(
                registry_config.json()).encode('utf-8')
            headers['X-Registry-Config'] = base64.b64encode(registry_config)

        # Request body
        if not os.path.exists(context):
            raise ValueError('context argument does not exist: %s' % (context))
        tar_buf = io.BytesIO()
        tar = tarfile.TarFile(fileobj=tar_buf, mode='w', dereference=True)
        if os.path.isfile(context):
            tar.add(context, 'Dockerfile')
        else:
            for f in os.listdir(context):
                tar.add(os.path.join(context, f), f)
        tar.close()

        # Query parameters
        query_params = {}
        no_cache = None if cache else True
        if force_rm:
            rm = None
        arg_fields = (
            ('dockerfile', (1, 17), 'dockerfile'),
            ('t', (1, 14), 'tag'),
            ('nocache', (1, 14), 'no_cache'),
            ('pull', (1, 16), 'pull'),
            ('rm', (1, 16), 'rm'),
            ('forcerm', (1, 16), 'force_rm'),
            ('buildargs', (1, 21), 'buildargs'),
            )
        json_update(query_params, locals(), arg_fields, self.api_version)
        host_config_fields = (
            ('memory', (1, 18), 'memory'),
            ('memswap', (1, 18), 'memory_swap'),
            ('cpushares', (1, 18), 'cpu_shares'),
            ('cpusetcpus', (1, 18), 'cpuset_cpus'),
            ('cpuperiod', (1, 19), 'cpu_period'),
            ('cpuquota', (1, 19), 'cpu_quota'),
            ('shmsize', (1, 22), 'shm_size'),
            )
        if host_config:
            json_update(query_params, host_config, host_config_fields,
                        self.api_version)

        r = self._post('/build', headers=headers, data=tar_buf.getvalue(),
                       params=query_params, stream=True)
        false_or_last_line = self._process_response_output(
            r, output, last_line=True)
        if false_or_last_line is False:
            return None
        id_match = re.match('Successfully built ([0-9a-f]+)',
                            false_or_last_line['stream'])
        return id_match.group(1)

    def image_pull(self, name, registry_auth=None,
                   output=('error', 'stream', 'status')):
        """Pull image.

        Create an image by pulling it from a registry.

        Arguments:
        name -- name of the image to pull
        output -- tuple/list of with type of output information to allow
                  (Default: ('stream', 'status', 'error')).
        """
        params = {'fromImage': name}
        headers = {'content-type': 'application/json'}
        if registry_auth:
            if not isinstance(registry_auth, dict):
                raise TypeError('registry_auth must be dict: %s' % (
                    type(registry_auth)))
            registry_auth = json.dumps(registry_auth).encode('utf-8')
            headers['X-Registry-Auth'] = base64.b64encode(registry_auth)
        r = self._post('/images/create', headers=headers, params=params,
                       stream=True)
        return self._process_response_output(r, output)

    def image_remove(self, name):
        """Remove an image.

        Remove the image name from the filesystem.

        Arguments:
        name -- name of the image to remove
        """
        r = self._delete('/images/{}'.format(name))
        return json.loads(r.text)

    def image_tag(self, image, tag, force=False):
        """Tag an image.

        Add tag to an existing image.

        Arguments:
        image -- image to add tag to
        tag -- name of tag (REPOSITORY or REPOSITORY:TAG)
        """
        params = {}
        if ':' in tag:
            params['repo'], params['tag'] = tag.split(':', 1)
        else:
            params['repo'] = tag
        params['force'] = 1 if force else 0
        self._post('/images/{}/tag'.format(image), params=params)

    def container_create(
            self,
            config: ContainerConfig,
            name: Optional[Union[ContainerName, str]]=None,
            mounts: Optional[Sequence[VolumeMount]]=None,
            host_config: Optional[HostConfig]=None):
        """Create a new container.

        Create a new container based on existing image.

        Arguments:
        name -- name to assign to container
        mounts -- mount points in the container (list of strings)
        config -- ContainerConfig instance
        host_config -- HostConfig instance
        """

        # Handle convenience argument types
        if isinstance(name, str):
            name = ContainerName(name)

        query_params = {}
        arg_fields = (
            ('name', (1, 14), 'name'),
            )
        json_update(query_params, locals(), arg_fields, self.api_version)

        # TODO: implementing handling of 'mounts' argument...

        # and figure out how to handle verification of fx. image, user and
        # container name arguments.  Maybe subclass str for the various string
        # type arguments.

        headers = {'content-type': 'application/json'}
        json_params = {}
        if isinstance(config, str):
            config = ContainerConfig(config)
        if config:
            json_params.update(config.json(self.api_version))
        if host_config:
            json_params['HostConfig'] = host_config.json(self.api_version)
        if 'ExposedPorts' in json_params:
            json_params['ExposedPorts'] = {
                port: {} for port in json_params['ExposedPorts']}

        response = self._post('/containers/create', params=query_params,
                              headers=headers, data=json.dumps(json_params))
        response_json = response.json()
        return Container(self, id=response_json['Id'])
