import unittest
import mock
import tempfile
import shutil
import os
import requests
import requests_mock

from xd.docker.image import *
from xd.docker.client import *


class tests(unittest.case.TestCase):

    def setUp(self):
        self.client = DockerClient()

    def test_init_noargs(self):
        image = Image(self.client)
        self.assertIsInstance(image, Image)

    def test_init_args_dockerfile(self):
        image = Image(self.client,
                      context='/tmp/image-ctx', dockerfile='Dockerfile')
        self.assertIsInstance(image, Image)

    @mock.patch('requests.get')
    def test_inspect_by_id(self, get_mock):
        image = Image(self.client, 'b750fe79269d2ec9a3c593ef05b4332b1d1a02a62b4accb2c21d589ff2f5f2dc')
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
        image.inspect()
        self.assertTrue(get_mock.called)
        self.assertIsNotNone(image.size)
        self.assertIsNotNone(image.created)
        self.assertIsNotNone(image.parent)

    @mock.patch('requests.get')
    def test_inspect_by_tag(self, get_mock):
        image = Image(self.client, tags=['foobar'])
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
        image.inspect()
        self.assertTrue(get_mock.called)
        self.assertIsNotNone(image.size)
        self.assertIsNotNone(image.created)
        self.assertIsNotNone(image.parent)

    def test_inspect_by_nothing(self):
        image = Image(self.client)
        with self.assertRaises(AnonymousImage):
            image.inspect()
