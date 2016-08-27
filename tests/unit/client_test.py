import unittest
import mock
import pytest
import io
import contextlib
import tempfile
import shutil
import os
import re
import json
import copy
import subprocess

import requests
import requests_mock

from xd.docker.client import *
from xd.docker.container import *
from xd.docker.image import *
from xd.docker.parameters import *


class init_tests(unittest.case.TestCase):

    def test_init_noargs(self):
        client = DockerClient()
        self.assertIsNotNone(client)
        self.assertEqual(client.base_url,
                         'http+unix://%2Fvar%2Frun%2Fdocker.sock')

    def test_init_unix(self):
        client = DockerClient('unix:///var/run/docker.sock')
        self.assertIsNotNone(client)
        self.assertEqual(client.base_url,
                         'http+unix://%2Fvar%2Frun%2Fdocker.sock')

    def test_init_tcp(self):
        client = DockerClient('tcp://127.0.0.1:2375')
        self.assertIsNotNone(client)
        self.assertEqual(client.base_url, 'http://127.0.0.1:2375')

    def test_init_http(self):
        with self.assertRaises(ValueError):
            DockerClient('http://127.0.0.1:2375')

    def test_init_http_unix(self):
        with self.assertRaises(ValueError):
            DockerClient('http+unix://127.0.0.1:2375')

    def test_init_foobar(self):
        with self.assertRaises(ValueError):
            DockerClient('foobar')


class SimpleClientTestCase(unittest.case.TestCase):

    def setUp(self):
        self.client = DockerClient()
        requests.get = mock.MagicMock(
            return_value=requests_mock.version_response("1.22", "1.10.3"))


class ContextClientTestCase(unittest.case.TestCase):

    def setUp(self):
        self.client = DockerClient()
        requests.get = mock.MagicMock(
            return_value=requests_mock.version_response("1.22", "1.10.3"))
        self.context = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.context)


class version_tests(SimpleClientTestCase):

    @mock.patch('requests.get')
    def test_version(self, get_mock):
        get_mock.return_value = requests_mock.Response(json.dumps({
            "Version": "1.5.0",
            "Os": "linux",
            "KernelVersion": "3.18.5-tinycore64",
            "GoVersion": "go1.4.1",
            "GitCommit": "a8a31ef",
            "Arch": "amd64",
            "ApiVersion": "1.18",
            }), 200)
        versions = self.client.version()
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
    def test_version_httperror_404(self, get_mock):
        get_mock.return_value = requests_mock.Response(
            '404 page not found\n', 404)
        with self.assertRaises(ClientError):
            self.client.version()

    @mock.patch('requests.get')
    def test_version_httperror_500(self, get_mock):
        get_mock.return_value = requests_mock.Response(
            '500 internal server error\n', 500)
        with self.assertRaises(ServerError):
            self.client.version()

    @mock.patch('requests.get')
    def test_version_httperror_unknown(self, get_mock):
        get_mock.return_value = requests_mock.Response(
            '999 foobar\n', 999)
        with self.assertRaises(HTTPError):
            self.client.version()


class ping_tests(SimpleClientTestCase):

    @mock.patch('requests.get')
    def test_ping(self, get_mock):
        get_mock.return_value = requests_mock.Response('OK\n', 200)
        self.client.ping()
        self.assertTrue(get_mock.called)

    @mock.patch('requests.get')
    def test_ping_server_error(self, get_mock):
        get_mock.return_value = requests_mock.Response('Server Error\n', 500)
        with self.assertRaises(HTTPError):
            self.client.ping()


class containers_tests(SimpleClientTestCase):

    response = [{
        "Id": "8dfafdbc3a40",
        "Names":["/boring_feynman"],
        "Image": "ubuntu:latest",
        "ImageID": "d74508fb6632491cea586a1fd7d748dfc5274cd6fdfedee309ecdcbc2bf5cb82",
        "Command": "echo 1",
        "Created": 1367854155,
        "State": "Exited",
        "Status": "Exit 0",
        "Ports": [{"PrivatePort": 2222, "PublicPort": 3333, "Type": "tcp"}],
        "Labels": {
            "com.example.vendor": "Acme",
            "com.example.license": "GPL",
            "com.example.version": "1.0"
        },
        "SizeRw": 12288,
        "SizeRootFs": 0,
        "HostConfig": {
            "NetworkMode": "default"
        },
        "NetworkSettings": {
            "Networks": {
                "bridge": {
                    "IPAMConfig": None,
                    "Links": None,
                    "Aliases": None,
                    "NetworkID": "7ea29fc1412292a2d7bba362f9253545fecdfa8ce9a6e37dd10ba8bee7129812",
                    "EndpointID": "2cdc4edb1ded3631c81f57966563e5c8525b81121bb3706a9a9a3ae102711f3f",
                    "Gateway": "172.17.0.1",
                    "IPAddress": "172.17.0.2",
                    "IPPrefixLen": 16,
                    "IPv6Gateway": "",
                    "GlobalIPv6Address": "",
                    "GlobalIPv6PrefixLen": 0,
                    "MacAddress": "02:42:ac:11:00:02"
                }
            }
        },
        "Mounts": [
            {
                "Name": "fac362...80535",
                "Source": "/data",
                "Destination": "/data",
                "Driver": "local",
                "Mode": "ro,Z",
                "RW": False,
                "Propagation": ""
            }
        ]
    }, {
        "Id": "9cd87474be90",
        "Names":["/coolName"],
        "Image": "ubuntu:latest",
        "ImageID": "d74508fb6632491cea586a1fd7d748dfc5274cd6fdfedee309ecdcbc2bf5cb82",
        "Command": "echo 222222",
        "Created": 1367854155,
        "State": "Exited",
        "Status": "Exit 0",
        "Ports": [],
        "Labels": {},
        "SizeRw": 12288,
        "SizeRootFs": 0,
        "HostConfig": {
            "NetworkMode": "default"
        },
        "NetworkSettings": {
            "Networks": {
                "bridge": {
                    "IPAMConfig": None,
                    "Links": None,
                    "Aliases": None,
                    "NetworkID": "7ea29fc1412292a2d7bba362f9253545fecdfa8ce9a6e37dd10ba8bee7129812",
                    "EndpointID": "88eaed7b37b38c2a3f0c4bc796494fdf51b270c2d22656412a2ca5d559a64d7a",
                    "Gateway": "172.17.0.1",
                    "IPAddress": "172.17.0.8",
                    "IPPrefixLen": 16,
                    "IPv6Gateway": "",
                    "GlobalIPv6Address": "",
                    "GlobalIPv6PrefixLen": 0,
                    "MacAddress": "02:42:ac:11:00:08"
                }
            }
        },
        "Mounts": []
    }, {
        "Id": "3176a2479c92",
        "Names":["/sleepy_dog"],
        "Image": "ubuntu:latest",
        "ImageID": "d74508fb6632491cea586a1fd7d748dfc5274cd6fdfedee309ecdcbc2bf5cb82",
        "Command": "echo 3333333333333333",
        "Created": 1367854154,
        "State": "Exited",
        "Status": "Exit 0",
        "Ports":[],
        "Labels": {},
        "SizeRw":12288,
        "SizeRootFs":0,
        "HostConfig": {
            "NetworkMode": "default"
        },
        "NetworkSettings": {
            "Networks": {
                "bridge": {
                    "IPAMConfig": None,
                    "Links": None,
                    "Aliases": None,
                    "NetworkID": "7ea29fc1412292a2d7bba362f9253545fecdfa8ce9a6e37dd10ba8bee7129812",
                    "EndpointID": "8b27c041c30326d59cd6e6f510d4f8d1d570a228466f956edf7815508f78e30d",
                    "Gateway": "172.17.0.1",
                    "IPAddress": "172.17.0.6",
                    "IPPrefixLen": 16,
                    "IPv6Gateway": "",
                    "GlobalIPv6Address": "",
                    "GlobalIPv6PrefixLen": 0,
                    "MacAddress": "02:42:ac:11:00:06"
                }
            }
        },
        "Mounts": []
    }, {
        "Id": "4cb07b47f9fb",
        "Names":["/running_cat", "/sleepy_dog/cat"],
        "Image": "ubuntu:latest",
        "ImageID": "d74508fb6632491cea586a1fd7d748dfc5274cd6fdfedee309ecdcbc2bf5cb82",
        "Command": "echo 444444444444444444444444444444444",
        "Created": 1367854152,
        "State": "Exited",
        "Status": "Exit 0",
        "Ports": [],
        "Labels": {},
        "SizeRw": 12288,
        "SizeRootFs": 0,
        "HostConfig": {
            "NetworkMode": "default"
        },
        "NetworkSettings": {
            "Networks": {
                "bridge": {
                    "IPAMConfig": None,
                    "Links": None,
                    "Aliases": None,
                    "NetworkID": "7ea29fc1412292a2d7bba362f9253545fecdfa8ce9a6e37dd10ba8bee7129812",
                    "EndpointID": "d91c7b2f0644403d7ef3095985ea0e2370325cd2332ff3a3225c4247328e66e9",
                    "Gateway": "172.17.0.1",
                    "IPAddress": "172.17.0.5",
                    "IPPrefixLen": 16,
                    "IPv6Gateway": "",
                    "GlobalIPv6Address": "",
                    "GlobalIPv6PrefixLen": 0,
                    "MacAddress": "02:42:ac:11:00:05"
                }
            }
        },
        "Mounts": []
    }]

    @mock.patch('requests.get')
    def test_containers_1(self, get_mock):
        get_mock.return_value = requests_mock.Response(json.dumps(
            self.response[:1]), 200)
        containers = self.client.containers()
        assert get_mock.called
        assert len(containers) == 1
        c = containers[0]
        assert isinstance(c, Container)
        assert c.id == '8dfafdbc3a40'
        assert isinstance(c.image, Image)

    @mock.patch('requests.get')
    def test_containers_3(self, get_mock):
        get_mock.return_value = requests_mock.Response(json.dumps(
            self.response[:3]), 200)
        containers = self.client.containers()
        assert get_mock.called
        assert len(containers) == 3
        expected = ['8dfafdbc3a40', '9cd87474be90', '3176a2479c92']
        for c in containers:
            assert isinstance(c, Container)
            assert c.id in expected
            expected.remove(c.id)
        assert expected == []

    @mock.patch('requests.get')
    def test_containers_4(self, get_mock):
        get_mock.return_value = requests_mock.Response(json.dumps(
            self.response), 200)
        containers = self.client.containers()
        assert get_mock.called
        assert len(containers) == 4
        expected = ['8dfafdbc3a40', '9cd87474be90',
                    '3176a2479c92', '4cb07b47f9fb']
        for c in containers:
            assert isinstance(c, Container)
            assert c.id in expected
            expected.remove(c.id)
            if c.id == '4cb07b47f9fb':
                assert c.name == '/running_cat'
                assert c.names == [('/sleepy_dog', 'cat')]
        assert expected == []

    @mock.patch('requests.get')
    def test_containers_only_running_false(self, get_mock):
        get_mock.return_value = requests_mock.Response(json.dumps(
            self.response[:1]), 200)
        containers = self.client.containers(only_running=False)
        assert get_mock.called
        assert 'params' in get_mock.call_args[1]
        params = get_mock.call_args[1]['params']
        assert 'all' in params
        assert params['all'] is True


class images_tests(SimpleClientTestCase):

    response = [{
        "RepoTags": [
            "ubuntu:12.04",
            "ubuntu:precise",
            "ubuntu:latest"
        ],
        "Id": "8dbd9e392a964056420e5d58ca5cc376ef18e2de93b5cc90e868a1bbc8318c1c",
        "Created": 1365714795,
        "Size": 131506275,
        "VirtualSize": 131506275
    }, {
        "RepoTags": [
            "ubuntu:12.10",
            "ubuntu:quantal"
        ],
        "ParentId": "27cf784147099545",
        "Id": "b750fe79269d2ec9a3c593ef05b4332b1d1a02a62b4accb2c21d589ff2f5f2dc",
        "Created": 1364102658,
        "Size": 24653,
        "VirtualSize": 180116135
    }]

    @mock.patch('requests.get')
    def test_images(self, get_mock):
        get_mock.return_value = requests_mock.Response(json.dumps(
            self.response), 200)
        images = self.client.images()
        assert get_mock.called is True
        assert len(images) == 2
        for image in images:
            assert isinstance(image, Image)
        assert images[0].id == '8dbd9e392a964056420e5d58ca5cc376ef18e2de93b5cc90e868a1bbc8318c1c'
        assert images[0].size == 131506275
        assert images[1].id == 'b750fe79269d2ec9a3c593ef05b4332b1d1a02a62b4accb2c21d589ff2f5f2dc'


class image_inspect_tests(SimpleClientTestCase):

    response = {
        "Created": "2013-03-23T22:24:18.818426-07:00",
        "Container":
        "3d67245a8d72ecf13f33dffac9f79dcdf70f75acb84d308770391510e0c23ad0",
        "ContainerConfig": {
            "Hostname": "",
            "User": "",
            "AttachStdin": False,
            "AttachStdout": False,
            "AttachStderr": False,
            "PortSpecs": None,
            "Tty": True,
            "OpenStdin": True,
            "StdinOnce": False,
            "Env": None,
            "Cmd": ["/bin/bash"],
            "Dns": None,
            "Image": "ubuntu",
            "Labels": {
                "com.example.vendor": "Acme",
                "com.example.license": "GPL",
                "com.example.version": "1.0"
            },
            "Volumes": None,
            "VolumesFrom": "",
            "WorkingDir": ""
        },
        "Id": "b750fe79269d2ec9a3c593ef05b4332b1d1a02a62b4accb2c21d589ff2f5f2dc",
        "Parent": "27cf784147099545",
        "Size": 6824592
    }

    @mock.patch('requests.get')
    def test_image_inspect(self, get_mock):
        get_mock.return_value = requests_mock.Response(json.dumps(
            self.response), 200)
        image = self.client.image_inspect('foobar')
        self.assertTrue(get_mock.called)
        self.assertIsInstance(image, Image)
        self.assertEqual(image.size, 6824592)

    @mock.patch('requests.get')
    def test_image_inspect_raw(self, get_mock):
        get_mock.return_value = requests_mock.Response(json.dumps(
            self.response), 200)
        image = self.client.image_inspect_raw('foobar')
        self.assertTrue(get_mock.called)
        self.assertIsInstance(image, dict)
        self.assertEqual(image['Size'], 6824592)


class image_build_tests(ContextClientTestCase):

    dockerfile = '''\
FROM debian:jessie
RUN echo Hello world
'''

    @mock.patch('requests.post')
    def test_image_build(self, post_mock):
        out = io.StringIO()
        with open(os.path.join(self.context, 'Dockerfile'), 'w') as dockerfile:
            dockerfile.write(self.dockerfile)
        post_mock.return_value = requests_mock.Response('''\
{"stream":"Step 0 : FROM debian:jessie\\n"}
{"stream":" ---\\u003e 0e30e84e9513\\n"}
{"stream":"Step 1 : RUN echo Hello world\\n"}
{"stream":" ---\\u003e Using cache\\n"}
{"stream":" ---\\u003e e4d9194b48f8\\n"}
{"stream":"Successfully built e4d9194b48f8\\n"}
''', 200)
        with contextlib.redirect_stdout(out):
            self.assertEqual(self.client.image_build(self.context),
                             'e4d9194b48f8')
        self.assertRegex(out.getvalue(), '''\
Step 0 : FROM debian:jessie
 ---> [0-9a-f]+
Step 1 : RUN echo Hello world
 ---> Using cache
 ---> [0-9a-f]+
Successfully built [0-9a-f]+
''')

    @mock.patch('requests.post')
    def test_image_build_context_as_file(self, post_mock):
        out = io.StringIO()
        with open(os.path.join(self.context, 'Dockerfile'), 'w') as dockerfile:
            dockerfile.write('''\
FROM debian:jessie
RUN echo Hello world
''')
        post_mock.return_value = requests_mock.Response('''\
{"stream":"Step 0 : FROM debian:jessie\\n"}
{"stream":" ---\\u003e 0e30e84e9513\\n"}
{"stream":"Step 1 : RUN echo Hello world\\n"}
{"stream":" ---\\u003e Using cache\\n"}
{"stream":" ---\\u003e e4d9194b48f8\\n"}
{"stream":"Successfully built e4d9194b48f8\\n"}
''', 200)
        with contextlib.redirect_stdout(out):
            self.assertEqual(self.client.image_build(
                os.path.join(self.context, 'Dockerfile')), 'e4d9194b48f8')
        self.assertRegex(out.getvalue(), '''\
Step 0 : FROM debian:jessie
 ---> [0-9a-f]+
Step 1 : RUN echo Hello world
 ---> Using cache
 ---> [0-9a-f]+
Successfully built [0-9a-f]+
''')

    @mock.patch('requests.post')
    def test_image_build_nonstandard_dockerfile(self, post_mock):
        out = io.StringIO()
        with open(os.path.join(self.context, 'DockerfileX'), 'w') as dockerfile:
            dockerfile.write('''\
FROM debian:jessie
RUN echo Hello world
''')
        post_mock.return_value = requests_mock.Response('''\
{"stream":"Step 0 : FROM debian:jessie\\n"}
{"stream":" ---\\u003e 0e30e84e9513\\n"}
{"stream":"Step 1 : RUN echo Hello world\\n"}
{"stream":" ---\\u003e Using cache\\n"}
{"stream":" ---\\u003e e4d9194b48f8\\n"}
{"stream":"Successfully built e4d9194b48f8\\n"}
''', 200)
        with contextlib.redirect_stdout(out):
            self.assertEqual(self.client.image_build(
                self.context, dockerfile='DockerfileX'), 'e4d9194b48f8')
        self.assertRegex(out.getvalue(), '''\
Step 0 : FROM debian:jessie
 ---> [0-9a-f]+
Step 1 : RUN echo Hello world
 ---> Using cache
 ---> [0-9a-f]+
Successfully built [0-9a-f]+
''')

    @mock.patch('requests.post')
    def test_image_build_with_name(self, post_mock):
        out = io.StringIO()
        with open(os.path.join(self.context, 'Dockerfile'), 'w') as dockerfile:
            dockerfile.write('''\
FROM debian:jessie
RUN echo Hello world
''')
        post_mock.return_value = requests_mock.Response('''\
{"stream":"Step 0 : FROM debian:jessie\\n"}
{"stream":" ---\\u003e 0e30e84e9513\\n"}
{"stream":"Step 1 : RUN echo Hello world\\n"}
{"stream":" ---\\u003e Using cache\\n"}
{"stream":" ---\\u003e e4d9194b48f8\\n"}
{"stream":"Successfully built e4d9194b48f8\\n"}
''', 200)
        with contextlib.redirect_stdout(out):
            self.assertEqual(self.client.image_build(
                self.context, tag='xd-docker-unittest:REMOVE'),
                'e4d9194b48f8')
        self.assertRegex(out.getvalue(), '''\
Step 0 : FROM debian:jessie
 ---> [0-9a-f]+
Step 1 : RUN echo Hello world
 ---> Using cache
 ---> [0-9a-f]+
Successfully built [0-9a-f]+
''')

    @mock.patch('requests.post')
    def test_image_build_with_nocache(self, post_mock):
        out = io.StringIO()
        with open(os.path.join(self.context, 'Dockerfile'), 'w') as dockerfile:
            dockerfile.write('''\
FROM debian:jessie
RUN echo Hello world
''')
        post_mock.return_value = requests_mock.Response('''\
{"stream":"Step 0 : FROM debian:jessie\\n"}
{"stream":" ---\\u003e 0e30e84e9513\\n"}
{"stream":"Step 1 : RUN echo Hello world\\n"}
{"stream":" ---> Running in e4d9194b48f8"}
{"stream":"Hello world\\n"}
{"stream":" ---\\u003e e4d9194b48f8\\n"}
{"stream":"Successfully built e4d9194b48f8\\n"}
''', 200)
        with contextlib.redirect_stdout(out):
            self.assertEqual(self.client.image_build(
                self.context, cache=False), 'e4d9194b48f8')
        self.assertRegex(out.getvalue(), '''\
Step 0 : FROM debian:jessie
 ---> [0-9a-f]+
Step 1 : RUN echo Hello world
 ---> Running in [0-9a-f]+
Hello world
 ---> [0-9a-f]+
Successfully built [0-9a-f]+
''')
        kwargs = post_mock.call_args[1]
        self.assertEqual(kwargs['params'], {'nocache': 1})

    @mock.patch('requests.post')
    def test_image_build_with_norm(self, post_mock):
        out = io.StringIO()
        with open(os.path.join(self.context, 'Dockerfile'), 'w') as dockerfile:
            dockerfile.write('''\
FROM debian:jessie
RUN echo Hello world
''')
        post_mock.return_value = requests_mock.Response('''\
{"stream":"Step 0 : FROM debian:jessie\\n"}
{"stream":" ---\\u003e 0e30e84e9513\\n"}
{"stream":"Step 1 : RUN echo Hello world\\n"}
{"stream":" ---\\u003e Using cache\\n"}
{"stream":" ---\\u003e e4d9194b48f8\\n"}
{"stream":"Successfully built e4d9194b48f8\\n"}
''', 200)
        with contextlib.redirect_stdout(out):
            self.assertEqual(self.client.image_build(
                self.context, rm=False), 'e4d9194b48f8')
        self.assertRegex(out.getvalue(), '''\
Step 0 : FROM debian:jessie
 ---> [0-9a-f]+
Step 1 : RUN echo Hello world
 ---> Using cache
 ---> [0-9a-f]+
Successfully built [0-9a-f]+
''')
        kwargs = post_mock.call_args[1]
        self.assertEqual(kwargs['params'], {'rm': 0})

    @mock.patch('requests.post')
    def test_image_build_with_forcerm(self, post_mock):
        out = io.StringIO()
        with open(os.path.join(self.context, 'Dockerfile'), 'w') as dockerfile:
            dockerfile.write('''\
FROM debian:jessie
RUN echo Hello world
''')
        post_mock.return_value = requests_mock.Response('''\
{"stream":"Step 0 : FROM debian:jessie\\n"}
{"stream":" ---\\u003e 0e30e84e9513\\n"}
{"stream":"Step 1 : RUN echo Hello world\\n"}
{"stream":" ---\\u003e Using cache\\n"}
{"stream":" ---\\u003e e4d9194b48f8\\n"}
{"stream":"Successfully built e4d9194b48f8\\n"}
''', 200)
        with contextlib.redirect_stdout(out):
            self.assertEqual(self.client.image_build(
                self.context, force_rm=True), 'e4d9194b48f8')
        self.assertRegex(out.getvalue(), '''\
Step 0 : FROM debian:jessie
 ---> [0-9a-f]+
Step 1 : RUN echo Hello world
 ---> Using cache
 ---> [0-9a-f]+
Successfully built [0-9a-f]+
''')
        kwargs = post_mock.call_args[1]
        self.assertEqual(kwargs['params'], {'forcerm': 1})

    @mock.patch('requests.post')
    def test_image_build_with_args(self, post_mock):
        out = io.StringIO()
        with open(os.path.join(self.context, 'Dockerfile'), 'w') as dockerfile:
            dockerfile.write('''\
FROM debian:jessie
RUN echo Hello world
''')
        post_mock.return_value = requests_mock.Response('''\
{"stream":"Step 0 : FROM debian:jessie\\n"}
{"stream":" ---\\u003e 0e30e84e9513\\n"}
{"stream":"Step 1 : RUN echo Hello world\\n"}
{"stream":" ---\\u003e Using cache\\n"}
{"stream":" ---\\u003e e4d9194b48f8\\n"}
{"stream":"Successfully built e4d9194b48f8\\n"}
''', 200)
        with contextlib.redirect_stdout(out):
            self.assertEqual(self.client.image_build(
                self.context, host_config=HostConfig(
                    memory=10000000, swap=2000000,
                    cpu_shares=42, cpuset_cpus='0-3')), 'e4d9194b48f8')
        self.assertRegex(out.getvalue(), '''\
Step 0 : FROM debian:jessie
 ---> [0-9a-f]+
Step 1 : RUN echo Hello world
 ---> Using cache
 ---> [0-9a-f]+
Successfully built [0-9a-f]+
''')
        kwargs = post_mock.call_args[1]
        self.assertEqual(kwargs['params'],
                         {'memory': 10000000, 'memswap': 12000000,
                          'cpushares': 42, 'cpusetcpus': '0-3'})

    @mock.patch('requests.post')
    def test_image_build_with_only_error_output(self, post_mock):
        out = io.StringIO()
        with open(os.path.join(self.context, 'Dockerfile'), 'w') as dockerfile:
            dockerfile.write('''\
FROM debian:jessie
RUN echo Hello world
''')
        post_mock.return_value = requests_mock.Response('''\
{"stream":"Step 0 : FROM debian:jessie\\n"}
{"stream":" ---\\u003e 0e30e84e9513\\n"}
{"stream":"Step 1 : RUN echo Hello world\\n"}
{"stream":" ---\\u003e Using cache\\n"}
{"stream":" ---\\u003e e4d9194b48f8\\n"}
{"stream":"Successfully built e4d9194b48f8\\n"}
''', 200)
        with contextlib.redirect_stdout(out):
            self.assertEqual(self.client.image_build(
                self.context, tag='xd-docker-unittest:REMOVE'),
                'e4d9194b48f8')
        self.assertRegex(out.getvalue(), '''\
Step 0 : FROM debian:jessie
 ---> [0-9a-f]+
Step 1 : RUN echo Hello world
( ---> Using cache|\
 ---> Running in [0-9a-f]+
Hello world)
 ---> [0-9a-f]+
Successfully built [0-9a-f]+
''')

    @mock.patch('requests.post')
    def test_image_build_with_registry_config(self, post_mock):
        out = io.StringIO()
        with open(os.path.join(self.context, 'Dockerfile'), 'w') as dockerfile:
            dockerfile.write('''\
FROM debian:jessie
RUN echo Hello world
''')
        post_mock.return_value = requests_mock.Response('''\
{"stream":"Step 0 : FROM debian:jessie\\n"}
{"stream":" ---\\u003e 0e30e84e9513\\n"}
{"stream":"Step 1 : RUN echo Hello world\\n"}
{"stream":" ---\\u003e Using cache\\n"}
{"stream":" ---\\u003e e4d9194b48f8\\n"}
{"stream":"Successfully built e4d9194b48f8\\n"}
''', 200)
        with contextlib.redirect_stdout(out):
            self.assertEqual(self.client.image_build(
                self.context, registry_config=RegistryAuthConfig({
                    "https://index.docker.io/v1/":
                    CredentialAuthConfig("myusername", "mypassword"),
                    "docker.example.com":
                    CredentialAuthConfig("othername", "otherpassword")
                })), 'e4d9194b48f8')
        self.assertRegex(out.getvalue(), '''\
Step 0 : FROM debian:jessie
 ---> [0-9a-f]+
Step 1 : RUN echo Hello world
( ---> Using cache|\
 ---> Running in [0-9a-f]+
Hello world)
 ---> [0-9a-f]+
Successfully built [0-9a-f]+
''')

    @mock.patch('requests.post')
    def test_image_build_with_pull(self, post_mock):
        out = io.StringIO()
        with open(os.path.join(self.context, 'Dockerfile'), 'w') as dockerfile:
            dockerfile.write('''\
FROM debian:jessie
RUN echo Hello world
''')
        post_mock.return_value = requests_mock.Response('''\
{"stream":"Step 0 : FROM debian:jessie\\n"}
{"status":"Pulling repository debian"}
{"status":"Pulling image (jessie) from debian","progressDetail":{},"id":"41b730702607"}{"status":"Pulling image (jessie) from debian, endpoint: https://registry-1.docker.io/v1/","progressDetail":{},"id":"41b730702607"}{"status":"Pulling dependent layers","progressDetail":{},"id":"41b730702607"}{"status":"Download complete","progressDetail":{},"id":"3cb35ae859e7"}{"status":"Download complete","progressDetail":{},"id":"41b730702607"}{"status":"Download complete","progressDetail":{},"id":"41b730702607"}{"status":"Status: Image is up to date for debian:jessie"}
{"stream":" ---\\u003e 0e30e84e9513\\n"}
{"stream":"Step 1 : RUN echo Hello world\\n"}
{"stream":" ---\\u003e Using cache\\n"}
{"stream":" ---\\u003e e4d9194b48f8\\n"}
{"stream":"Successfully built e4d9194b48f8\\n"}
''', 200)
        with contextlib.redirect_stdout(out):
            self.assertEqual(self.client.image_build(
                self.context, pull=True), 'e4d9194b48f8')
        self.assertRegex(out.getvalue(), '''\
Step 0 : FROM debian:jessie
Pulling repository debian
Status: Image is up to date for debian:jessie
 ---> [0-9a-f]+
Step 1 : RUN echo Hello world
 ---> Using cache
 ---> [0-9a-f]+
Successfully built [0-9a-f]+
''')
        kwargs = post_mock.call_args[1]
        self.assertEqual(kwargs['params'], {'pull': 1})

    @mock.patch('requests.post')
    def test_image_build_server_error(self, post_mock):
        with open(os.path.join(self.context, 'Dockerfile'), 'w') as dockerfile:
            dockerfile.write('''\
FROM debian:jessie
RUN echo Hello world
''')
        post_mock.return_value = requests_mock.Response('Server Error\n', 500)
        with self.assertRaises(HTTPError):
            self.client.image_build(self.context)

    @mock.patch('requests.post')
    def test_image_build_invalid_tag_1(self, post_mock):
        with open(os.path.join(self.context, 'Dockerfile'), 'w') as dockerfile:
            dockerfile.write('''\
FROM debian:jessie
RUN echo Hello world
''')
        with self.assertRaises(TypeError):
            self.client.image_build(self.context, tag=42)

    @mock.patch('requests.post')
    def test_image_build_invalid_tag_2(self, post_mock):
        with open(os.path.join(self.context, 'Dockerfile'), 'w') as dockerfile:
            dockerfile.write('''\
FROM debian:jessie
RUN echo Hello world
''')
        with self.assertRaises(ValueError):
            self.client.image_build(self.context, tag='foo:bar:hello')

    @mock.patch('requests.post')
    def test_image_build_invalid_rm(self, post_mock):
        with open(os.path.join(self.context, 'Dockerfile'), 'w') as dockerfile:
            dockerfile.write('''\
FROM debian:jessie
RUN echo Hello world
''')
        with self.assertRaises(TypeError):
            self.client.image_build(self.context, rm=42)

    @mock.patch('requests.post')
    def test_image_build_invalid_pull(self, post_mock):
        with open(os.path.join(self.context, 'Dockerfile'), 'w') as dockerfile:
            dockerfile.write('''\
FROM debian:jessie
RUN echo Hello world
''')
        with self.assertRaises(TypeError):
            self.client.image_build(self.context, pull=42)

    @mock.patch('requests.post')
    def test_image_build_context_does_not_exist(self, post_mock):
        post_mock.return_value = requests_mock.Response('Server Error\n', 500)
        with self.assertRaises(ValueError):
            self.client.image_build(os.path.join(self.context, 'MISSING'))

    @mock.patch('requests.post')
    def test_image_build_run_error(self, post_mock):
        out = io.StringIO()
        with open(os.path.join(self.context, 'Dockerfile'), 'w') as dockerfile:
            dockerfile.write('''\
FROM debian:jessie
RUN false
''')
        post_mock.return_value = requests_mock.Response('''\
{"stream":"Step 0 : FROM debian:jessie"}
{"stream":" ---> 0e30e84e9513"}
{"stream":"Step 1 : RUN false"}
{"stream":" ---> Running in e4d9194b48f8"}
{"error":"The command [/bin/sh -c false] returned a non-zero code: 1","errorDetail":{"message":"The command [/bin/sh -c false] returned a non-zero code: 1"}}
''', 200)
        with contextlib.redirect_stdout(out):
            self.assertIsNone(self.client.image_build(self.context))


class image_pull_tests(ContextClientTestCase):

    ok_response = '''\
{"status": "Pulling from library/busybox\\n"}
{"status": "Already exists\\n"}
{"status": "Already exists\\n"}
{"status": "Already exists\\n"}
{"status": "Already exists\\n"}
{"status": "Digest: sha256:38a203e1986cf79639cfb9b2e1d6e773de84002feea2d4eb006b52004ee8502d\\n"}
{"status": "Status: Image is up to date for busybox:latest\\n"}
'''

    not_found_response = '{"error": "Error: image library/nosuchthingshouldexist: not found"}'

    @mock.patch('requests.post')
    def test_image_pull_1_ok(self, post_mock):
        out = io.StringIO()
        post_mock.return_value = requests_mock.Response(self.ok_response, 200)
        with contextlib.redirect_stdout(out):
            self.client.image_pull('busybox')
        self.assertRegex(out.getvalue(),
                         'Status: (Image is up to date|Downloaded newer image) '
                         'for busybox:latest')

    @mock.patch('requests.post')
    def test_image_pull_2_not_found(self, post_mock):
        out = io.StringIO()
        post_mock.return_value = requests_mock.Response(self.not_found_response, 200)
        with contextlib.redirect_stdout(out):
            self.client.image_pull('nosuchthingshouldexist', output=('error'))
        self.assertRegex(out.getvalue(), 'nosuchthingshouldexist\: not found')

    @mock.patch('requests.post')
    def test_image_pull_3_authconfig(self, post_mock):
        out = io.StringIO()
        post_mock.return_value = requests_mock.Response(self.ok_response, 200)
        with contextlib.redirect_stdout(out):
            self.client.image_pull('busybox:latest', registry_auth={
                'username': 'user',
                'password': 'secret',
                'email': 'user@domain.com',
                'serveraddress': 'domain.com'})
        self.assertRegex(out.getvalue(),
                         'Status: (Image is up to date|Downloaded newer image) '
                         'for busybox:latest')

    @mock.patch('requests.post')
    def test_image_pull_4_invalid_authconfig(self, post_mock):
        with self.assertRaises(TypeError):
            self.client.image_pull('busybox:latest', registry_auth=42)


class image_remove_tests(ContextClientTestCase):

    @mock.patch('requests.delete')
    def test_image_remove_1(self, delete_mock):
        delete_mock.return_value = requests_mock.Response(json.dumps([
            {"Untagged": "3e2f21a89f"},
            {"Deleted": "3e2f21a89f"},
            {"Deleted": "53b4f83ac9"}
        ]), 200)
        self.assertIsNotNone(self.client.image_remove('busybox:latest'))

    @mock.patch('requests.delete')
    def test_image_remove_2_not_found(self, delete_mock):
        delete_mock.return_value = requests_mock.Response('', 400)
        with self.assertRaises(HTTPError):
            self.client.image_remove('busybox:latest')


class image_tag_tests(ContextClientTestCase):

    @mock.patch('requests.post')
    def test_image_tag_1_repo(self, post_mock):
        post_mock.return_value = requests_mock.Response('', 201)
        self.client.image_tag('busybox:latest', 'myrepo')

    @mock.patch('requests.post')
    def test_image_tag_2_repo_and_tag(self, post_mock):
        post_mock.return_value = requests_mock.Response('', 201)
        self.client.image_tag('busybox:latest', 'myrepo:tag')

    @mock.patch('requests.post')
    def test_image_tag_3_force(self, post_mock):
        post_mock.return_value = requests_mock.Response('', 201)
        self.client.image_tag('busybox:latest', 'myrepo', force=True)

    @mock.patch('requests.post')
    def test_image_tag_4_fail(self, post_mock):
        post_mock.return_value = requests_mock.Response('', 409)
        with self.assertRaises(HTTPError):
            self.client.image_tag('busybox:latest', 'myrepo')


class container_create_tests(ContextClientTestCase):

    simple_success_response = requests_mock.Response(json.dumps({
        "Id": "e90e34656806",
        "Warnings": []}), 200)

    @mock.patch('requests.post')
    def test_container_create_1_anon(self, post_mock):
        post_mock.return_value = self.simple_success_response
        container = self.client.container_create(ContainerConfig('busybox:latest'))
        self.assertIsInstance(container, Container)
        (args, kwargs) = post_mock.call_args
        self.assertIn('data', kwargs)
        data_arg = json.loads(kwargs['data'])
        self.assertNotIn('OomKillDisable', data_arg)
        self.assertNotIn('NetworkDisable', data_arg)
        self.assertNotIn('Env', data_arg)

    @mock.patch('requests.post')
    def test_container_create_2_named(self, post_mock):
        post_mock.return_value = self.simple_success_response
        container = self.client.container_create(
            ContainerConfig('busybox:latest'), name='xd-docker-unittest')
        self.assertIsInstance(container, Container)

    @mock.patch('requests.post')
    def test_container_create_3_named_str(self, post_mock):
        post_mock.return_value = self.simple_success_response
        container = self.client.container_create(
            'busybox:latest', name='xd-docker-unittest')
        self.assertIsInstance(container, Container)

    @mock.patch('requests.post')
    def test_container_create_with_command(self, post_mock):
        post_mock.return_value = self.simple_success_response
        container = self.client.container_create(
            ContainerConfig('busybox:latest', command='/bin/sh'))
        self.assertIsInstance(container, Container)

    @mock.patch('requests.post')
    def test_container_create_with_memory(self, post_mock):
        post_mock.return_value = self.simple_success_response
        self.client.container_create(
            ContainerConfig('busybox:latest'),
            host_config = HostConfig(memory=1024*1024))

    @mock.patch('requests.post')
    def test_container_create_with_memory_and_swap(self, post_mock):
        post_mock.return_value = self.simple_success_response
        self.client.container_create(
            ContainerConfig('busybox:latest'),
            host_config = HostConfig(memory=1024*1024, swap=2*1024*1024))

    def test_container_create_with_swap_but_not_memory(self):
        with self.assertRaises(ValueError):
            self.client.container_create(
                ContainerConfig('busybox:latest'),
                host_config = HostConfig(swap=1024*1024))

    @mock.patch('requests.post')
    def test_container_create_with_oom_kill_false(self, post_mock):
        post_mock.return_value = self.simple_success_response
        self.client.container_create(
            ContainerConfig('busybox:latest'),
            host_config = HostConfig(oom_kill=False))
        (args, kwargs) = post_mock.call_args
        self.assertIn('data', kwargs)
        data_arg = json.loads(kwargs['data'])
        self.assertIn('HostConfig', data_arg)
        host_config = data_arg['HostConfig']
        self.assertIn('OomKillDisable', host_config)
        self.assertTrue(host_config['OomKillDisable'])

    @mock.patch('requests.post')
    def test_container_create_with_network_false(self, post_mock):
        post_mock.return_value = self.simple_success_response
        self.client.container_create(
            ContainerConfig('busybox:latest',network=False))
        (args, kwargs) = post_mock.call_args
        self.assertIn('data', kwargs)
        data_arg = json.loads(kwargs['data'])
        self.assertIn('NetworkDisabled', data_arg)
        self.assertTrue(data_arg['NetworkDisabled'])

    @mock.patch('requests.post')
    def test_container_create_with_env(self, post_mock):
        post_mock.return_value = self.simple_success_response
        self.client.container_create(
            ContainerConfig('busybox:latest',
                            env={'foo': '42', 'bar': '43'}))
        (args, kwargs) = post_mock.call_args
        self.assertIn('data', kwargs)
        data_arg = json.loads(kwargs['data'])
        self.assertIn('Env', data_arg)
        env_arg = sorted(data_arg['Env'])
        self.assertEqual(env_arg, ['bar=43', 'foo=42'])

    @mock.patch('requests.post')
    def test_container_create_with_exposed_ports(self, post_mock):
        post_mock.return_value = self.simple_success_response
        self.client.container_create(
            ContainerConfig('busybox:latest',
                            exposed_ports=['22/tcp', '80/tcp']))
        (args, kwargs) = post_mock.call_args
        self.assertIn('data', kwargs)
        data_arg = json.loads(kwargs['data'])
        self.assertIn('ExposedPorts', data_arg)
        exposed_ports_arg = data_arg['ExposedPorts']
        print(exposed_ports_arg)
        self.assertEqual(exposed_ports_arg, {'22/tcp': {}, '80/tcp': {}})

    @mock.patch('requests.get')
    @mock.patch('requests.post')
    def test_container_create_pull_needed(self, post_mock, get_mock):
        post_mock.return_value = self.simple_success_response
        get_mock.side_effect = [
            requests_mock.version_response("1.22", "1.10.3"),
            requests_mock.Response('404 no such image\n', 404)]
        self.client.container_create(
            ContainerConfig('busybox:latest'), pull=True)
        assert post_mock.call_count == 2
        name, args, kwargs = post_mock.mock_calls[1]
        assert args[0].endswith('/containers/create')

    @mock.patch('requests.get')
    @mock.patch('requests.post')
    def test_container_create_pull_not_needed(self, post_mock, get_mock):
        post_mock.return_value = self.simple_success_response
        get_mock.side_effect = [
            requests_mock.version_response("1.22", "1.10.3"),
            requests_mock.Response(json.dumps(
                image_inspect_tests.response), 200)]
        self.client.container_create(
            ContainerConfig('busybox:latest'), pull=True)
        assert post_mock.call_count == 1
        name, args, kwargs = post_mock.mock_calls[0]
        assert args[0].endswith('/containers/create')

    @mock.patch('requests.get')
    @mock.patch('requests.post')
    def test_container_create_nopull_needed(self, post_mock, get_mock):
        post_mock.return_value = self.simple_success_response
        get_mock.side_effect = [
            requests_mock.version_response("1.22", "1.10.3"),
            requests_mock.Response('404 no such image\n', 404)]
        self.client.container_create(
            ContainerConfig('busybox:latest'), pull=False)
        assert post_mock.call_count == 1
        name, args, kwargs = post_mock.mock_calls[0]
        assert args[0].endswith('/containers/create')

    @mock.patch('requests.get')
    @mock.patch('requests.post')
    def test_container_create_nopull_not_needed(self, post_mock, get_mock):
        post_mock.return_value = self.simple_success_response
        get_mock.side_effect = [
            requests_mock.version_response("1.22", "1.10.3"),
            requests_mock.Response(json.dumps(
                image_inspect_tests.response), 200)]
        self.client.container_create(
            ContainerConfig('busybox:latest'), pull=False)
        assert post_mock.call_count == 1
        name, args, kwargs = post_mock.mock_calls[0]
        assert args[0].endswith('/containers/create')


class container_remove_tests(ContextClientTestCase):

    @mock.patch('requests.delete')
    def test_ok(self, delete_mock):
        delete_mock.return_value = requests_mock.Response("OK", 200)
        self.client.container_remove('foobar')
        params = delete_mock.call_args[1]['params']
        assert 'force' not in params
        assert 'v' not in params
        assert delete_mock.call_args[0][0].endswith('/containers/foobar')

    @mock.patch('requests.delete')
    def test_no_such_container(self, delete_mock):
        delete_mock.return_value = requests_mock.Response(
            "No such container", 404)
        with pytest.raises(ClientError) as clienterror:
            self.client.container_remove('foobar')
        assert clienterror.value.code == 404

    @mock.patch('requests.delete')
    def test_containername(self, delete_mock):
        delete_mock.return_value = requests_mock.Response("OK", 200)
        self.client.container_remove(ContainerName('foobar'))
        assert delete_mock.call_args[0][0].endswith('/containers/foobar')

    @mock.patch('requests.delete')
    def test_container_with_name(self, delete_mock):
        delete_mock.return_value = requests_mock.Response("OK", 200)
        self.client.container_remove(Container(self.client, name='foobar'))
        assert delete_mock.call_args[0][0].endswith('/containers/foobar')

    @mock.patch('requests.delete')
    def test_container_with_id(self, delete_mock):
        delete_mock.return_value = requests_mock.Response("OK", 200)
        self.client.container_remove(Container(self.client, id='dfeb03b02b41'))
        assert delete_mock.call_args[0][0].endswith('/containers/dfeb03b02b41')

    @mock.patch('requests.delete')
    def test_container_with_id_and_name(self, delete_mock):
        delete_mock.return_value = requests_mock.Response("OK", 200)
        self.client.container_remove(Container(self.client,
                                               id='dfeb03b02b41', name='foo'))
        assert delete_mock.call_args[0][0].endswith('/containers/dfeb03b02b41')

    @mock.patch('requests.delete')
    def test_force_true(self, delete_mock):
        delete_mock.return_value = requests_mock.Response("OK", 200)
        self.client.container_remove('foobar', force=True)
        params = delete_mock.call_args[1]['params']
        assert 'force' in params and params['force']

    @mock.patch('requests.delete')
    def test_force_false(self, delete_mock):
        delete_mock.return_value = requests_mock.Response("OK", 200)
        self.client.container_remove('foobar', force=False)
        params = delete_mock.call_args[1]['params']
        assert 'force' in params and not params['force']

    @mock.patch('requests.delete')
    def test_volumes_true(self, delete_mock):
        delete_mock.return_value = requests_mock.Response("OK", 200)
        self.client.container_remove('foobar', volumes=True)
        params = delete_mock.call_args[1]['params']
        assert 'v' in params and params['v']

    @mock.patch('requests.delete')
    def test_volumes_false(self, delete_mock):
        delete_mock.return_value = requests_mock.Response("OK", 200)
        self.client.container_remove('foobar', volumes=False)
        params = delete_mock.call_args[1]['params']
        assert 'v' in params and not params['v']


class container_start_tests(ContextClientTestCase):

    @mock.patch('requests.post')
    def test_str(self, post_mock):
        post_mock.return_value = requests_mock.Response("OK", 204)
        assert self.client.container_start('foobar')
        assert not post_mock.call_args[1]['params']
        assert post_mock.call_args[0][0].endswith('/containers/foobar/start')

    @mock.patch('requests.post')
    def test_containername(self, post_mock):
        post_mock.return_value = requests_mock.Response("OK", 204)
        assert self.client.container_start(ContainerName('foobar'))
        assert not post_mock.call_args[1]['params']
        assert post_mock.call_args[0][0].endswith('/containers/foobar/start')

    @mock.patch('requests.post')
    def test_container_with_name(self, post_mock):
        post_mock.return_value = requests_mock.Response("OK", 204)
        assert self.client.container_start(
            Container(self.client, name='foobar'))
        assert post_mock.call_args[0][0].endswith('/containers/foobar/start')

    @mock.patch('requests.post')
    def test_container_with_id(self, post_mock):
        post_mock.return_value = requests_mock.Response("OK", 204)
        assert self.client.container_start(
            Container(self.client, id='dfeb03b02b41'))
        assert post_mock.call_args[0][0].endswith(
            '/containers/dfeb03b02b41/start')

    @mock.patch('requests.post')
    def test_container_with_id_and_name(self, post_mock):
        post_mock.return_value = requests_mock.Response("OK", 204)
        assert self.client.container_start(
            Container(self.client, id='dfeb03b02b41', name='foobar'))
        assert post_mock.call_args[0][0].endswith(
            '/containers/dfeb03b02b41/start')

    @mock.patch('requests.post')
    def test_already_running(self, post_mock):
        post_mock.return_value = requests_mock.Response(
            "Container already started", 304)
        assert not self.client.container_start('foobar')

    @mock.patch('requests.post')
    def test_no_such_container(self, post_mock):
        post_mock.return_value = requests_mock.Response(
            "No such container", 404)
        with pytest.raises(ClientError) as clienterror:
            self.client.container_start('foobar')
        assert clienterror.value.code == 404


class container_wait_tests(ContextClientTestCase):

    @mock.patch('requests.post')
    def test_0(self, post_mock):
        post_mock.return_value = requests_mock.Response(json.dumps(
            {'StatusCode': 0}), 200)
        assert self.client.container_wait("foobar") == 0

    @mock.patch('requests.post')
    def test_42(self, post_mock):
        post_mock.return_value = requests_mock.Response(json.dumps(
            {'StatusCode': 42}), 200)
        assert self.client.container_wait("foobar") == 42

    @mock.patch('requests.post')
    def test_no_such_container(self, post_mock):
        post_mock.return_value = requests_mock.Response(None, 404)
        with pytest.raises(ClientError) as clienterror:
            self.client.container_wait('foobar')
        assert clienterror.value.code == 404

    @mock.patch('requests.post')
    def test_containername(self, post_mock):
        post_mock.return_value = requests_mock.Response(json.dumps(
            {'StatusCode': 0}), 200)
        assert self.client.container_wait(ContainerName("foobar")) == 0

    @mock.patch('requests.post')
    def test_container(self, post_mock):
        post_mock.return_value = requests_mock.Response(json.dumps(
            {'StatusCode': 0}), 200)
        assert self.client.container_wait(Container(
            self.client,name="foobar")) == 0


class container_stop_tests(ContextClientTestCase):

    @mock.patch('requests.post')
    def test_normal(self, post_mock):
        post_mock.return_value = requests_mock.Response(None, 204)
        assert self.client.container_stop("foobar") == True

    @mock.patch('requests.post')
    def test_already_stopped(self, post_mock):
        post_mock.return_value = requests_mock.Response(None, 304)
        assert self.client.container_stop("foobar") == False

    @mock.patch('requests.post')
    def test_no_such_container(self, post_mock):
        post_mock.return_value = requests_mock.Response(None, 404)
        with pytest.raises(ClientError) as clienterror:
            self.client.container_stop('foobar')
        assert clienterror.value.code == 404

    @mock.patch('requests.post')
    def test_containername(self, post_mock):
        post_mock.return_value = requests_mock.Response(None, 204)
        assert self.client.container_stop(ContainerName("foobar")) == True

    @mock.patch('requests.post')
    def test_container(self, post_mock):
        post_mock.return_value = requests_mock.Response(None, 204)
        assert self.client.container_stop(Container(
            self.client,name="foobar")) == True

    @mock.patch('requests.post')
    def test_timeout(self, post_mock):
        post_mock.return_value = requests_mock.Response(None, 204)
        assert self.client.container_stop("foobar", timeout=42) == True
        assert 'params' in post_mock.call_args[1]
        params = post_mock.call_args[1]['params']
        assert 't' in params
        assert params['t'] == 42
