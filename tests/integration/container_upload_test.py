import pytest
import os
import io
import tarfile
import re

from xd.docker.client import *


def test_upload(docker, stdout, cleandir):
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
