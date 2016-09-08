import pytest
import os
import io
import tarfile
import re

from xd.docker.client import *
from xd.docker.exceptions import *

DOCKER_VERSION = tuple(map(int, (os.getenv('DOCKER_VERSION').split('.'))))


@pytest.mark.skipif(DOCKER_VERSION < (1,8),
                    reason="Upload support was added in Docker 1.8")
def test_upload(docker, cleandir):
    tar_buf = io.BytesIO()
    tar_file = tarfile.TarFile(fileobj=tar_buf, mode='w', dereference=True)
    with open('foo', 'w') as f:
        f.write('foobarx\n')
    tar_file.add('foo')
    os.system("docker create --name xd-docker-test busybox:latest cat /foo")
    docker.container_upload('xd-docker-test', tar_buf.getvalue(), '/')
    os.system("docker start -a xd-docker-test > bar")
    with open('bar', 'r') as f:
        result = f.read()
    assert re.match('foobar', result, re.M)


@pytest.mark.skipif(DOCKER_VERSION >= (1,8),
                    reason="Upload support was added in Docker 1.8")
def test_incompatible(docker, cleandir):
    tar_buf = io.BytesIO()
    tar_file = tarfile.TarFile(fileobj=tar_buf, mode='w', dereference=True)
    with open('foo', 'w') as f:
        f.write('foobarx\n')
    tar_file.add('foo')
    with pytest.raises(IncompatibleRemoteAPI):
        docker.container_upload('xd-docker-test', tar_buf.getvalue(), '/')
