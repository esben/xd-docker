"""Module containing DockerClient and associated exceptions."""

import logging
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


import urllib.parse
import requests
import requests_unixsocket
requests_unixsocket.monkeypatch()
import json
import base64
import os
import io
import tarfile
import re


from xd.docker.container import *
from xd.docker.image import *


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


def parse_kwargs(allowed_kwargs, kwargs):
    params = {}
    for arg_name, param_name, validator in allowed_kwargs:
        try:
            arg = kwargs.pop(arg_name)
        except KeyError:
            continue
        if arg is None:
            continue
        if isinstance(validator, type):
            if not isinstance(arg, validator):
                raise TypeError("invalid '%s' argument: %s" % (
                    arg_name, repr(arg)))
        else:
            assert callable(validator)
            try:
                if not validator(arg):
                    raise ValueError("invalid '%s' argument: %s" % (
                        arg_name, repr(arg)))
            except TypeError:
                raise TypeError("invalid '%s' argument: %s" % (
                    arg_name, repr(arg)))
        param_name = param_name.split('.')
        p = params
        while len(param_name) > 1:
            pn = param_name.pop(0)
            if pn not in p:
                p[pn] = {}
            p = p[pn]
        pn = param_name.pop()
        p[pn] = arg
    return params


def is_image_name(name):
    if not isinstance(name, str):
        raise TypeError()
    if name.count(':') > 1:
        return False
    return True


def is_bool_or_force(arg):
    if isinstance(arg, bool):
        return True
    if arg == 'force':
        return True
    return False


class DockerClient(object):
    """Docker client."""

    def __init__(self, host=None):
        """Docker client concstructor."""
        if host is None:
            host = 'unix:///var/run/docker.sock'
        if host.startswith('unix://'):
            host = 'http+unix://' + urllib.parse.quote_plus(host[7:])
        elif host.startswith('tcp://'):
            host = 'http://' + host[6:]
        else:
            raise ValueError('Invalid host value: {}'.format(host))
        self.base_url = host

    def _check_http_status_code(self, url, status_code):
        if status_code >= 200 and status_code < 300:
            return
        elif status_code >= 400 and status_code <= 499:
            raise ClientError(url, status_code)
        elif status_code >= 500 and status_code <= 599:
            raise ServerError(url, status_code)
        else:
            raise HTTPError(url, status_code)

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

    def version(self):
        """Get Docker Remote API version."""
        r = self._get('/version')
        version = json.loads(r.text)
        return version

    def ping(self):
        """Ping the docker server."""
        self._get('/_ping')

    def containers(self, all_=False):
        """Get list of containers.

        By default, only running containers are returned.

        Keyword arguments:
        all_ -- return all containers if True.
        """
        params = {}
        params['all'] = all_
        r = self._get('/containers/json', params=params)
        containers = {}
        for c in json.loads(r.text):
            containers[c['Id']] = DockerContainer(self, list_response=c)
        return containers

    def images(self):
        """Get list of images.

        Returns list of DockerImage instances of all images.
        """
        r = self._get('/images/json')
        images = {}
        for c in json.loads(r.text):
            images[c['Id']] = DockerImage(
                self, id_=c['Id'], created=c['Created'], tags=c['RepoTags'],
                size=c['Size'], virtual_size=c['VirtualSize'])
        return images

    def image_inspect(self, name, raw=False):
        """Get image with low-level information.

        Get low-level information of a named image.  Returns DockerImage
        instance with the information.

        Arguments:
        name -- name of image.

        Keyword arguments:
        raw -- if True, return the low-level image information in raw format
               instaed of DockerImage instance.
        """
        r = self._get('/images/{}/json'.format(name))
        i = json.loads(r.text)
        if raw:
            return i
        else:
            return DockerImage(
                self, id_=i['Id'], created=i['Created'], size=i['Size'],
                parent=i['Parent'])

    def image_build(self, context, registry_config=None,
                    output=('error', 'stream', 'status'), **kwargs):
        """Build image.

        Build image from a given context or stand-alone Dockerfile.

        Arguments:
        context -- path to directory containing build context, or path to a
                   stand-alone Dockerfile.

        Keyword arguments:
        dockerfile -- path to dockerfile in build context.
        name -- name (and optionally a tag) to be applied to the resulting
                image.
        nocache -- do not use the cache when building the image
                   (default: False).
        pull -- attempt to pull the image even if an older image exists locally.
                (default: False)
        rm -- False/True/'force'. Remove intermediate containers after a
              successful build, and if 'force', always do that.
              (default: True).
        memory -- set memory limit for build.
        memswap -- total memory (memory + swap), -1 to disable swap.
        cpushares -- CPU shares (relative weight).
        cpusetcpus -- CPUs in which to allow execution.
        registry_config -- dict containing ConfigFile object specification.
        output -- tuple/list of with type of output information to allow
                  (Default: ('stream', 'status', 'error')).
        """
        headers = {'content-type': 'application/tar'}
        if registry_config:
            if not isinstance(registry_config, dict):
                raise TypeError('registry_config must be dict: %s' % (
                    type(registry_config)))
            registry_config = json.dumps(registry_config).encode('utf-8')
            headers['X-Registry-Config'] = base64.b64encode(registry_config)
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
        params = parse_kwargs((
            ('dockerfile', 'dockerfile', str),
            ('name', 't', is_image_name),
            ('nocache', 'nocache', bool),
            ('pull', 'pull', bool),
            ('rm', 'rm', is_bool_or_force),
            ('memory', 'memory', int),
            ('memswap', 'memswap', int),
            ('cpushares', 'cpushares', int),
            ('cpusetcpus', 'cpusetcpus', str),
            ), kwargs)
        if 'rm' in params and params['rm'] == 'force':
            del params['rm']
            params['forcerm'] = True
        r = self._post('/build', headers=headers, data=tar_buf.getvalue(),
                       params=params, stream=True)
        decoder = json.JSONDecoder()
        failed = False
        for line in r.iter_lines():
            if not line:
                continue
            line = line.decode('utf-8')
            index = 0
            while index < len(line):
                data, extra_data_index = decoder.raw_decode(line[index:])
                index += extra_data_index
                for t in ('stream', 'status', 'error'):
                    if t in output and t in data:
                        print(data[t].rstrip('\n'))
                if 'error' in data:
                    failed = True
        if failed:
            return None
        id_match = re.match('Successfully built ([0-9a-f]+)', data['stream'])
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
        headers = { 'content-type': 'application/json' }
        if registry_auth:
            if not isinstance(registry_auth, dict):
                raise TypeError('registry_auth must be dict: %s'%(
                    type(registry_auth)))
            registry_auth = json.dumps(registry_auth).encode('utf-8')
            headers['X-Registry-Auth'] = base64.b64encode(registry_auth)
        r = self._post('/images/create', headers=headers, params=params,
                       stream=True)
        decoder = json.JSONDecoder()
        failed = False
        for line in r.iter_lines():
            line = line.decode('utf-8')
            index = 0
            while index < len(line):
                data, extra_data_index = decoder.raw_decode(line[index:])
                index += extra_data_index
                for t in ('stream', 'status', 'error'):
                    if t in output and t in data:
                        print(data[t].rstrip('\n'))
                if 'error' in data:
                    failed = True
        if failed:
            return None

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
