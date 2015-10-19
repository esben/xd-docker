import unittest
import mock

from xd.docker.container import *
from xd.docker.image import *
from xd.docker.client import *

class tests(unittest.case.TestCase):

    def setUp(self):
        self.client = DockerClient()

    def test_init_noargs(self):
        container = DockerContainer(self.client)
        self.assertIsInstance(container, DockerContainer)

    def test_init_id_only(self):
        container = DockerContainer(self.client, '0123456789abcdef'*4)
        self.assertIsInstance(container, DockerContainer)
        self.assertEqual(container.id, '0123456789abcdef'*4)

    def test_init_list_response(self):
        container = DockerContainer(
            self.client, list_response={
                'Id': '0123456789abcdef'*4,
                'Names': ['/foobar'],
                'Image': 'ubuntu:latest',
                'Command': 'echo Hello world',
                'Created': 1367854155,
                'Status': 'Exit 0',
                'Ports': [{'PrivatePort': 2222,
                           'PublicPort': 3333,
                           'Type': 'tcp'}],
                'Labels': {'foo.bar': '42',
                           'foo.BAR': '4242'},
                'SizeRW': 12288,
                'SizeRootFs': 0,
            })
        self.assertIsInstance(container, DockerContainer)
        self.assertEqual(container.id, '0123456789abcdef'*4)
        self.assertIsInstance(container.image, DockerImage)
        self.assertEqual(container.image.tags, ['ubuntu:latest'])
        self.assertEqual(container.command, 'echo Hello world')
        self.assertEqual(container.created, 1367854155)
        self.assertEqual(container.status, 'Exit 0')
        self.assertEqual(container.ports, [{'PrivatePort': 2222,
                                            'PublicPort': 3333,
                                            'Type': 'tcp'}])
        self.assertEqual(container.labels, {'foo.bar': '42',
                                            'foo.BAR': '4242'})
        self.assertEqual(container.sizerw, 12288)
        self.assertEqual(container.sizerootfs, 0)


    def test_init_inspect_response(self):
        container = DockerContainer(
            self.client, id='123456789abcdef'*4, inspect_response={
                "AppArmorProfile": "",
                "Args": [
                    "-c",
                    "exit 9"
                ],
                "Config": {
                    "AttachStderr": True,
                    "AttachStdin": False,
                    "AttachStdout": True,
                    "Cmd": [
                        "/bin/sh",
                        "-c",
                        "exit 9"
                    ],
                    "Domainname": "",
                    "Entrypoint": None,
                    "Env": [
                        "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
                    ],
                    "ExposedPorts": None,
                    "Hostname": "ba033ac44011",
                    "Image": "ubuntu",
                    "Labels": {
                        "com.example.vendor": "Acme",
                        "com.example.license": "GPL",
                        "com.example.version": "1.0"
                    },
                    "MacAddress": "",
                    "NetworkDisabled": False,
                    "OnBuild": None,
                    "OpenStdin": False,
                    "StdinOnce": False,
                    "Tty": False,
                    "User": "",
                    "Volumes": None,
                    "WorkingDir": ""
                },
                "Created": "2015-01-06T15:47:31.485331387Z",
                "Driver": "devicemapper",
                "ExecDriver": "native-0.2",
                "ExecIDs": None,
                "HostConfig": {
                    "Binds": None,
                    "BlkioWeight": 0,
                    "CapAdd": None,
                    "CapDrop": None,
                    "ContainerIDFile": "",
                    "CpusetCpus": "",
                    "CpusetMems": "",
                    "CpuShares": 0,
                    "CpuPeriod": 100000,
                    "Devices": [],
                    "Dns": None,
                    "DnsSearch": None,
                    "ExtraHosts": None,
                    "IpcMode": "",
                    "Links": None,
                    "LxcConf": [],
                    "Memory": 0,
                    "MemorySwap": 0,
                    "OomKillDisable": False,
                    "NetworkMode": "bridge",
                    "PortBindings": {},
                    "Privileged": False,
                    "ReadonlyRootfs": False,
                    "PublishAllPorts": False,
                    "RestartPolicy": {
                        "MaximumRetryCount": 2,
                        "Name": "on-failure"
                    },
                    "LogConfig": {
                        "Config": None,
                        "Type": "json-file"
                    },
                    "SecurityOpt": None,
                    "VolumesFrom": None,
                    "Ulimits": [{}]
                },
                "HostnamePath": "/var/lib/docker/containers/ba033ac4401106a3b513bc9d639eee123ad78ca3616b921167cd74b20e25ed39/hostname",
                "HostsPath": "/var/lib/docker/containers/ba033ac4401106a3b513bc9d639eee123ad78ca3616b921167cd74b20e25ed39/hosts",
                "LogPath": "/var/lib/docker/containers/1eb5fabf5a03807136561b3c00adcd2992b535d624d5e18b6cdc6a6844d9767b/1eb5fabf5a03807136561b3c00adcd2992b535d624d5e18b6cdc6a6844d9767b-json.log",
                "Id": "ba033ac4401106a3b513bc9d639eee123ad78ca3616b921167cd74b20e25ed39",
                "Image": "04c5d3b7b0656168630d3ba35d8889bd0e9caafcaeb3004d2bfbc47e7c5d35d2",
                "MountLabel": "",
                "Name": "/boring_euclid",
                "NetworkSettings": {
                    "Bridge": "",
                    "Gateway": "",
                    "IPAddress": "",
                    "IPPrefixLen": 0,
                    "MacAddress": "",
                    "PortMapping": None,
                    "Ports": None
                },
                "Path": "/bin/sh",
                "ProcessLabel": "",
                "ResolvConfPath": "/var/lib/docker/containers/ba033ac4401106a3b513bc9d639eee123ad78ca3616b921167cd74b20e25ed39/resolv.conf",
                "RestartCount": 1,
                "State": {
                    "Error": "",
                    "ExitCode": 9,
                    "FinishedAt": "2015-01-06T15:46:36.080254511Z",
                    "OOMKilled": False,
                    "Paused": False,
                    "Pid": 0,
                    "Restarting": False,
                    "Running": False,
                    "StartedAt": "2015-01-06T15:43:32.072697474Z"
                },
                "Mounts": [
                    {
                        "Source": "/data",
                        "Destination": "/data",
                        "Mode": "ro,Z",
                        "RW": False
                    }
                ]
            })
        self.assertIsNotNone(container, DockerContainer)
        et = container.state.execution_time
        self.assertEqual(et.days, 0)
        self.assertEqual(et.seconds, 184)
        self.assertEqual(et.microseconds, 7557)

    def test_init_inspect_response_partial(self):
        container = DockerContainer(
            self.client, id='123456789abcdef'*4, inspect_response={
                "AppArmorProfile": "",
                "Args": [
                    "-c",
                    "exit 9"
                ],
                "Config": {
                    "Cmd": [
                        "/bin/sh",
                        "-c",
                        "exit 9"
                    ],
                    "Entrypoint": None,
                    "Env": [
                        "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
                    ],
                    "Hostname": "ba033ac44011",
                    "Image": "ubuntu",
                    "Labels": {},
                    "Tty": False,
                    "User": "",
                    "Volumes": None,
                    "WorkingDir": ""
                },
                "Created": "2015-01-06T15:47:31.485331387Z",
                "HostConfig": {
                    "Binds": None,
                    "Ulimits": [{}]
                },
                "HostnamePath": "/var/lib/docker/containers/ba033ac4401106a3b513bc9d639eee123ad78ca3616b921167cd74b20e25ed39/hostname",
                "HostsPath": "/var/lib/docker/containers/ba033ac4401106a3b513bc9d639eee123ad78ca3616b921167cd74b20e25ed39/hosts",
                "LogPath": "/var/lib/docker/containers/1eb5fabf5a03807136561b3c00adcd2992b535d624d5e18b6cdc6a6844d9767b/1eb5fabf5a03807136561b3c00adcd2992b535d624d5e18b6cdc6a6844d9767b-json.log",
                "Id": "ba033ac4401106a3b513bc9d639eee123ad78ca3616b921167cd74b20e25ed39",
                "Image": "04c5d3b7b0656168630d3ba35d8889bd0e9caafcaeb3004d2bfbc47e7c5d35d2",
                "MountLabel": "",
                "Name": "/boring_euclid",
                "NetworkSettings": {
                    "Bridge": "",
                    "Gateway": "",
                    "IPAddress": "",
                    "IPPrefixLen": 0,
                    "MacAddress": "",
                    "PortMapping": None,
                    "Ports": None
                },
                "Path": "/bin/sh",
                "ProcessLabel": "",
                "ResolvConfPath": "/var/lib/docker/containers/ba033ac4401106a3b513bc9d639eee123ad78ca3616b921167cd74b20e25ed39/resolv.conf",
                "RestartCount": 1,
                "Mounts": [
                    {
                        "Source": "/data",
                        "Destination": "/data",
                        "Mode": "ro,Z",
                        "RW": False
                    }
                ]
            })
        self.assertIsNotNone(container, DockerContainer)
