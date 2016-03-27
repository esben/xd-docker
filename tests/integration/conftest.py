import pytest
import io
import contextlib
import tempfile
import shutil
import os

from xd.docker.client import *


DOCKER_HOST = os.environ.get('DOCKER_HOST', None)


@pytest.fixture(scope="module")
def docker(request):
    return DockerClient(host=DOCKER_HOST)


class StreamRedirector(object):

    def __init__(self):
        self.stream = io.StringIO()

    def redirect(self):
        return contextlib.redirect_stdout(self.stream)

    def get(self):
        return self.stream.getvalue()

    def getlines(self):
        return self.stream.getvalue().rstrip('\n').split('\n')

    def lastline(self):
        lines = self.getlines()
        if not lines:
            return None
        return lines[-1]


@pytest.fixture
def stdout():
    return StreamRedirector()


@pytest.fixture
def cleandir(request):
    newdir = tempfile.mkdtemp()
    os.chdir(newdir)
    def remove_cleandir():
        shutil.rmtree(newdir)
    request.addfinalizer(remove_cleandir)
    return newdir
