import unittest
import mock
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
        "Image": "ubuntu:latest",
        "Command": "echo 1",
        "Created": 1367854155,
        "Status": "Up 42 seconds",
        "Ports": [
            {"PrivatePort": 2222,
             "PublicPort": 3333,
             "Type": "tcp"}],
        "SizeRw": 12288,
        "SizeRootFs": 0
    }, {
        "Id": "9cd87474be90",
        "Image": "ubuntu:latest",
        "Command": "echo 222222",
        "Created": 1367854155,
        "Status": "Up 666 seconds",
        "Ports": [],
        "SizeRw": 12288,
        "SizeRootFs": 0
    }]

    @mock.patch('requests.get')
    def test_containers(self, get_mock):
        get_mock.return_value = requests_mock.Response(json.dumps(
            self.response), 200)
        containers = self.client.containers()
        self.assertTrue(get_mock.called)
        self.assertEqual(len(containers), 2)
        for container in containers.values():
            self.assertIsInstance(container, Container)
            self.assertIsInstance(container.image, Image)
        self.assertIn('8dfafdbc3a40', containers)
        self.assertIn('9cd87474be90', containers)

    @mock.patch('requests.get')
    def test_containers_all(self, get_mock):
        response = copy.deepcopy(self.response)
        response[1]['Status'] = 'Exit 0'
        get_mock.return_value = requests_mock.Response(json.dumps(
            self.response), 200)
        containers = self.client.containers(all_=True)
        self.assertTrue(get_mock.called)
        self.assertEqual(len(containers), 2)
        for container in containers.values():
            self.assertIsInstance(container, Container)
            self.assertIsInstance(container.image, Image)
        self.assertIn('8dfafdbc3a40', containers)
        self.assertIn('9cd87474be90', containers)


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
        self.assertTrue(get_mock.called)
        self.assertEqual(len(images), 2)
        for image in images.values():
            self.assertIsInstance(image, Image)
        self.assertIn(
            '8dbd9e392a964056420e5d58ca5cc376ef18e2de93b5cc90e868a1bbc8318c1c',
            images)
        self.assertIn(
            'b750fe79269d2ec9a3c593ef05b4332b1d1a02a62b4accb2c21d589ff2f5f2dc',
            images)
        self.assertEqual(images[
            '8dbd9e392a964056420e5d58ca5cc376ef18e2de93b5cc90e868a1bbc8318c1c'
        ].size, 131506275)


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
        image = self.client.image_inspect('foobar', raw=True)
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
