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

