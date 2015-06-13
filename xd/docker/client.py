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


__all__ = ['DockerClient', 'HTTPError']


class HTTPError(Exception):
    def __init__(self, url, code):
        self.url = url
        self.code = code


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

    def _get(self, url, params=None, stream=False, ok_status_codes=[200]):
        url = self.base_url + url
        r = requests.get(url, params=params, stream=stream)
        if r.status_code not in ok_status_codes:
            raise HTTPError(url, r.status_code)
        return r

    def _post(self, url, params=None, headers=None, data=None,
              stream=False, ok_status_codes=[200]):
        url = self.base_url + url
        r = requests.post(url, params=params, headers=headers, data=data,
                          stream=stream)
        if r.status_code not in ok_status_codes:
            raise HTTPError(url, r.status_code)
        return r

    def version(self):
        r = self._get('/version')
        version = json.loads(r.text)
        return version

    def ping(self):
        self._get('/_ping')

    def containers(self, all_=False):
        params = {}
        params['all'] = all_
        r = self._get('/containers/json', params=params)
        containers = {}
        for c in json.loads(r.text):
            containers[c['Id']] = DockerContainer(
                self, id_=c['Id'], names=c.get('Names', []),
                command=c['Command'], ports=c['Ports'],
                image=c['Image'], created=c['Created'])
        return containers

    def images(self):
        r = self._get('/images/json')
        images = {}
        for c in json.loads(r.text):
            images[c['Id']] = DockerImage(
                self, id_=c['Id'], created=c['Created'], tags=c['RepoTags'],
                size=c['Size'], virtual_size=c['VirtualSize'])
        return images

    def image_inspect(self, name, raw=False):
        r = self._get('/images/{}/json'.format(name))
        i = json.loads(r.text)
        if raw:
            return i
        else:
            return DockerImage(
                self, id_=i['Id'], created=i['Created'], size=i['Size'],
                parent=i['Parent'])

    def image_build(self, context, dockerfile=None, name=None,
                    nocache=False, pull=False, rm=True,
                    memory=None, memswap=None, cpushares=None, cpusetcpus=None,
                    registry_config=None, output=('error', 'stream', 'status')):
        headers = { 'content-type': 'application/tar' }
        if registry_config:
            if not isinstance(registry_config, dict):
                raise TypeError('registry_config must be dict: %s'%(
                    type(registry_config)))
            registry_config = json.dumps(registry_config).encode('utf-8')
            headers['X-Registry-Config'] = base64.b64encode(registry_config)
        if not os.path.exists(context):
            raise ValueError('context argument does not exist: %s'%(context))
        tar_buf = io.BytesIO()
        tar = tarfile.TarFile(fileobj=tar_buf, mode='w', dereference=True)
        if os.path.isfile(context):
            tar.add(context, 'Dockerfile')
        else:
            for f in os.listdir(context):
                tar.add(os.path.join(context, f), f)
        tar.close()
        params = {}
        if dockerfile:
            params['dockerfile'] = dockerfile
        if name:
            params['t'] = name
        if nocache:
            params['nocache'] = 1
        if pull:
            params['pull'] = 1
        if not rm:
            params['rm'] = 0
        if rm == 'force':
            params['forcerm'] = 1
        if memory is not None:
            params['memory'] = memory
        if memswap is not None:
            params['memswap'] = memswap
        if cpushares is not None:
            params['cpushares'] = cpushares
        if cpusetcpus is not None:
            params['cpusetcpus'] = cpusetcpus
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
