import pytest
import os

from xd.docker.client import *


def test_restart(docker, stdout):
    os.system("docker run -d --name xd-docker-test busybox:latest sleep 5")
    docker.container_restart('xd-docker-test')


def test_already_stopped(docker, stdout):
    os.system("docker run --name xd-docker-test busybox:latest true")
    docker.container_restart('xd-docker-test')


def test_not_started(docker, stdout):
    os.system("docker create --name xd-docker-test busybox:latest true")
    docker.container_restart('xd-docker-test')


def test_no_such_container(docker, stdout):
    with pytest.raises(ClientError) as clienterror:
        with stdout.redirect():
            docker.container_stop('xd-docker-test')
    assert clienterror.value.code == 404
