import logging
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


import urllib.parse
import requests
import requests_unixsocket
requests_unixsocket.monkeypatch()
import json


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
        self.base_url = host

    def version(self):
        url = self.base_url + '/version'
        r = requests.get(url)
        if r.status_code != 200:
            raise HTTPError(url, r.status_code)
        version = json.loads(r.text)
        return version
