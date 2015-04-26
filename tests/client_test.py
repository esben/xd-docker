import unittest
import mock

import requests_mock

from xd.docker.client import *

class tests(unittest.case.TestCase):

    def test_init_noargs(self):
        client = DockerClient()
        self.assertIsNotNone(client)

    def test_init_args(self):
        client = DockerClient('tcp://127.0.0.1:2375')
        self.assertIsNotNone(client)

    @mock.patch('requests.get')
    def test_version(self, get_mock):
        client = DockerClient()
        get_mock.return_value = requests_mock.Response(
            '''{
            "Version": "1.5.0",
            "Os": "linux",
            "KernelVersion": "3.18.5-tinycore64",
            "GoVersion": "go1.4.1",
            "GitCommit": "a8a31ef",
            "Arch": "amd64",
            "ApiVersion": "1.18"
}\n''', 200)
        versions = client.version()
        self.assertTrue(get_mock.called)
        self.assertIn('Version', versions)
        self.assertEqual(versions['Version'], '1.5.0')
        self.assertIn('ApiVersion', versions)
        self.assertEqual(versions['ApiVersion'], '1.18')
        api = versions['ApiVersion'].split('.')
        api = [int(s) for s in api]
        if api[0] >= 1 and api[1] >= 18:
            self.assertIn('Os', versions)
            self.assertEqual(versions['Os'], 'linux')
            self.assertIn('Arch', versions)
            self.assertEqual(versions['Arch'], 'amd64')

    @mock.patch('requests.get')
    def test_version_httperror(self, get_mock):
        client = DockerClient()
        get_mock.return_value = requests_mock.Response(
            '404 page not found\n', 404)
        with self.assertRaises(HTTPError):
            client.version()

    @mock.patch('requests.get')
    def test_ping(self, get_mock):
        client = DockerClient()
        get_mock.return_value = requests_mock.Response('OK\n', 200)
        client.ping()
        self.assertTrue(get_mock.called)

    @mock.patch('requests.get')
    def test_ping_server_error(self, get_mock):
        client = DockerClient()
        get_mock.return_value = requests_mock.Response('Server Error\n', 500)
        with self.assertRaises(HTTPError):
            client.ping()
