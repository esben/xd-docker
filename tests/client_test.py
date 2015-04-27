import unittest
import mock

import requests_mock

from xd.docker.client import *
from xd.docker.container import *
from xd.docker.image import *

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

    @mock.patch('requests.get')
    def test_containers(self, get_mock):
        client = DockerClient()
        get_mock.return_value = requests_mock.Response(
            '''[
            {
            "Id": "8dfafdbc3a40",
            "Image": "ubuntu:latest",
            "Command": "echo 1",
            "Created": 1367854155,
            "Status": "Up 42 seconds",
            "Ports": [{"PrivatePort": 2222, "PublicPort": 3333, "Type": "tcp"}],
            "SizeRw": 12288,
            "SizeRootFs": 0
            },
            {
            "Id": "9cd87474be90",
            "Image": "ubuntu:latest",
            "Command": "echo 222222",
            "Created": 1367854155,
            "Status": "Up 666 seconds",
            "Ports": [],
            "SizeRw": 12288,
            "SizeRootFs": 0
            }
]\n''', 200)
        containers = client.containers()
        self.assertTrue(get_mock.called)
        self.assertEqual(len(containers), 2)
        for container in containers.values():
            self.assertIsInstance(container, DockerContainer)
            self.assertIsInstance(container.image, DockerImage)
        self.assertIn('8dfafdbc3a40', containers)
        self.assertIn('9cd87474be90', containers)

    @mock.patch('requests.get')
    def test_containers_all(self, get_mock):
        client = DockerClient()
        get_mock.return_value = requests_mock.Response(
            '''[
            {
            "Id": "3176a2479c92",
            "Image": "ubuntu:latest",
            "Command": "echo 3333333333333333",
            "Created": 1367854154,
            "Status": "Exit 0",
            "Ports":[],
            "SizeRw":12288,
            "SizeRootFs":0
            },
            {
            "Id": "4cb07b47f9fb",
            "Image": "ubuntu:latest",
            "Command": "echo 444444444444444444444444444444444",
            "Created": 1367854152,
            "Status": "Exit 0",
            "Ports": [],
            "SizeRw": 12288,
            "SizeRootFs": 0
            }
]\n''', 200)
        containers = client.containers()
        self.assertTrue(get_mock.called)
        self.assertEqual(len(containers), 2)
        for container in containers.values():
            self.assertIsInstance(container, DockerContainer)
            self.assertIsInstance(container.image, DockerImage)
        self.assertIn('3176a2479c92', containers)
        self.assertIn('4cb07b47f9fb', containers)

    @mock.patch('requests.get')
    def test_images(self, get_mock):
        client = DockerClient()
        get_mock.return_value = requests_mock.Response('''\
[
  {
    "RepoTags": [
      "ubuntu:12.04",
      "ubuntu:precise",
      "ubuntu:latest"
    ],
    "Id": "8dbd9e392a964056420e5d58ca5cc376ef18e2de93b5cc90e868a1bbc8318c1c",
    "Created": 1365714795,
    "Size": 131506275,
    "VirtualSize": 131506275
  },
  {
    "RepoTags": [
      "ubuntu:12.10",
      "ubuntu:quantal"
    ],
    "ParentId": "27cf784147099545",
    "Id": "b750fe79269d2ec9a3c593ef05b4332b1d1a02a62b4accb2c21d589ff2f5f2dc",
    "Created": 1364102658,
    "Size": 24653,
    "VirtualSize": 180116135
  }
]
''', 200)
        images = client.images()
        self.assertTrue(get_mock.called)
        self.assertEqual(len(images), 2)
        for image in images.values():
            self.assertIsInstance(image, DockerImage)
        self.assertIn('8dbd9e392a964056420e5d58ca5cc376ef18e2de93b5cc90e868a1bbc8318c1c', images)
        self.assertIn('b750fe79269d2ec9a3c593ef05b4332b1d1a02a62b4accb2c21d589ff2f5f2dc', images)
        self.assertEqual(images['8dbd9e392a964056420e5d58ca5cc376ef18e2de93b5cc90e868a1bbc8318c1c'].size, 131506275)

    @mock.patch('requests.get')
    def test_image_inspect(self, get_mock):
        client = DockerClient()
        get_mock.return_value = requests_mock.Response('''\
{
  "Created": "2013-03-23T22:24:18.818426-07:00",
  "Container": "3d67245a8d72ecf13f33dffac9f79dcdf70f75acb84d308770391510e0c23ad0",
  "ContainerConfig": {
    "Hostname": "",
    "User": "",
    "AttachStdin": false,
    "AttachStdout": false,
    "AttachStderr": false,
    "PortSpecs": null,
    "Tty": true,
    "OpenStdin": true,
    "StdinOnce": false,
    "Env": null,
    "Cmd": ["/bin/bash"],
    "Dns": null,
    "Image": "ubuntu",
    "Labels": {
        "com.example.vendor": "Acme",
        "com.example.license": "GPL",
        "com.example.version": "1.0"
    },
    "Volumes": null,
    "VolumesFrom": "",
    "WorkingDir": ""
  },
  "Id": "b750fe79269d2ec9a3c593ef05b4332b1d1a02a62b4accb2c21d589ff2f5f2dc",
  "Parent": "27cf784147099545",
  "Size": 6824592
}
''', 200)
        image = client.image_inspect('foobar')
        self.assertTrue(get_mock.called)
        self.assertIsInstance(image, DockerImage)
        self.assertEqual(image.size, 6824592)

    @mock.patch('requests.get')
    def test_image_inspect_raw(self, get_mock):
        client = DockerClient()
        get_mock.return_value = requests_mock.Response('''\
{
  "Created": "2013-03-23T22:24:18.818426-07:00",
  "Container": "3d67245a8d72ecf13f33dffac9f79dcdf70f75acb84d308770391510e0c23ad0",
  "ContainerConfig": {
    "Hostname": "",
    "User": "",
    "AttachStdin": false,
    "AttachStdout": false,
    "AttachStderr": false,
    "PortSpecs": null,
    "Tty": true,
    "OpenStdin": true,
    "StdinOnce": false,
    "Env": null,
    "Cmd": ["/bin/bash"],
    "Dns": null,
    "Image": "ubuntu",
    "Labels": {
        "com.example.vendor": "Acme",
        "com.example.license": "GPL",
        "com.example.version": "1.0"
    },
    "Volumes": null,
    "VolumesFrom": "",
    "WorkingDir": ""
  },
  "Id": "b750fe79269d2ec9a3c593ef05b4332b1d1a02a62b4accb2c21d589ff2f5f2dc",
  "Parent": "27cf784147099545",
  "Size": 6824592
}
''', 200)
        image = client.image_inspect('foobar', raw=True)
        self.assertTrue(get_mock.called)
        self.assertIsInstance(image, dict)
        self.assertEqual(image['Size'], 6824592)
