import logging
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


import urllib.parse
import requests
import requests_unixsocket
requests_unixsocket.monkeypatch()
import json


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

    def _get(self, url, params=None, ok_status_codes=[200]):
        url = self.base_url + url
        r = requests.get(url, params=params)
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
