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

    def _get(self, url, ok_status_codes=[200]):
        url = self.base_url + url
        r = requests.get(url)
        if r.status_code not in ok_status_codes:
            raise HTTPError(url, r.status_code)
        return r

    def version(self):
        r = self._get('/version')
        version = json.loads(r.text)
        return version
