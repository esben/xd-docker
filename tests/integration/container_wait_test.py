import pytest
import os
import time

from xd.docker.client import *


def test_waiting(docker, stdout):
    os.system("docker run -d --name xd-docker-test busybox:latest sleep 2")
    assert docker.container_wait('xd-docker-test') == 0


def test_already_stopped_0(docker, stdout):
    os.system("docker run --name xd-docker-test busybox:latest true")
    assert docker.container_wait('xd-docker-test') == 0


def test_already_stopped_1(docker, stdout):
    os.system("docker run --name xd-docker-test busybox:latest false")
    assert docker.container_wait('xd-docker-test') == 1


def test_no_such_container(docker, stdout):
    with pytest.raises(ClientError) as clienterror:
        with stdout.redirect():
            docker.container_wait('xd-docker-test')
    assert clienterror.value.code == 404
