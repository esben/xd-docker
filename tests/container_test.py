import unittest
import mock

from xd.docker.container import *
from xd.docker.client import *

class tests(unittest.case.TestCase):

    def setUp(self):
        self.client = DockerClient()

    def test_init_noargs(self):
        container = DockerContainer(self.client)
        self.assertIsInstance(container, DockerContainer)

    def test_init_args(self):
        container = DockerContainer(self.client,
                                    id_='123456789abcdef', names=['foo', 'bar'],
                                    command=['uname'], ports=[], image='ubuntu',
                                    created=1234567)
        self.assertIsNotNone(container, DockerContainer)

