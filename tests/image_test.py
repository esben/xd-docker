import unittest
import mock
import tempfile
import shutil
import os

import requests_mock

from xd.docker.image import *
from xd.docker.client import *

class tests(unittest.case.TestCase):

    def setUp(self):
        self.client = DockerClient()

    def test_init_noargs(self):
        image = DockerImage(self.client)
        self.assertIsInstance(image, DockerImage)

    def test_init_args_created(self):
        image = DockerImage(self.client,
                            id_='123456789abcdef', created=1234567)
        self.assertIsInstance(image, DockerImage)

    def test_init_args_dockerfile(self):
        image = DockerImage(self.client,
                            context='/tmp/image-ctx', dockerfile='Dockerfile')
        self.assertIsInstance(image, DockerImage)

    @mock.patch('requests.get')
    def test_inspect_by_id(self, get_mock):
        image = DockerImage(self.client, id_='b750fe79269d2ec9a3c593ef05b4332b1d1a02a62b4accb2c21d589ff2f5f2dc')
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
        image = DockerImage(self.client, tags=['foobar'])
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
        image = DockerImage(self.client)
        with self.assertRaises(AnonymousImage):
            image.inspect()


class build_tests(unittest.case.TestCase):

    def setUp(self):
        self.client = DockerClient()
        self.context = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.context)

    @mock.patch('requests.post')
    def test_build(self, post_mock):
        with open(os.path.join(self.context, 'Dockerfile'), 'w') as dockerfile:
            dockerfile.write('''\
FROM debian:jessie
RUN echo Hello world
''')
        image = DockerImage(self.client, context=self.context)
        post_mock.return_value = requests_mock.Response('''\
{"stream":"Step 0 : FROM debian:jessie\\n"}
{"stream":" ---\\u003e 0e30e84e9513\\n"}
{"stream":"Step 1 : RUN echo Hello world\\n"}
{"stream":" ---\\u003e Using cache\\n"}
{"stream":" ---\\u003e e4d9194b48f8\\n"}
{"stream":"Successfully built e4d9194b48f8\\n"}
''', 200)
        image.build()
        self.assertEqual(image.id, 'e4d9194b48f8')
        kwargs = post_mock.call_args[1]
        self.assertEqual(kwargs['params'], {})

    @mock.patch('requests.post')
    def test_build_and_tag(self, post_mock):
        with open(os.path.join(self.context, 'Dockerfile'), 'w') as dockerfile:
            dockerfile.write('''\
FROM debian:jessie
RUN echo Hello world
''')
        image = DockerImage(self.client, context=self.context)
        post_mock.return_value = requests_mock.Response('''\
{"stream":"Step 0 : FROM debian:jessie\\n"}
{"stream":" ---\\u003e 0e30e84e9513\\n"}
{"stream":"Step 1 : RUN echo Hello world\\n"}
{"stream":" ---\\u003e Using cache\\n"}
{"stream":" ---\\u003e e4d9194b48f8\\n"}
{"stream":"Successfully built e4d9194b48f8\\n"}
''', 200)
        image.build(name='xd-docker-unittest')
        self.assertEqual(image.id, 'e4d9194b48f8')
        kwargs = post_mock.call_args[1]
        self.assertEqual(kwargs['params'], {'t': 'xd-docker-unittest'})
