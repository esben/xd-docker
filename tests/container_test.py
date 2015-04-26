import unittest
import mock

from xd.docker.container import *

class tests(unittest.case.TestCase):

    def test_init_noargs(self):
        container = DockerContainer()
        self.assertIsInstance(container, DockerContainer)

    def test_init_args(self):
        container = DockerContainer(id_='123456789abcdef', names=['foo', 'bar'],
                                    command=['uname'], ports=[], image='ubuntu',
                                    created=1234567)
        self.assertIsNotNone(container, DockerContainer)

