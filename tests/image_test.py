import unittest
import mock

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
