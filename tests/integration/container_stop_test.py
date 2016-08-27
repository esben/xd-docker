import pytest
import os
import time

from xd.docker.client import *


def test_stop(docker, stdout):
    os.system("docker run -d --name xd-docker-test busybox:latest sleep 10")
    assert docker.container_stop('xd-docker-test') == True


def test_already_stopped(docker, stdout):
    os.system("docker run --name xd-docker-test busybox:latest true")
    assert docker.container_stop('xd-docker-test') == False


def test_not_started(docker, stdout):
    os.system("docker create --name xd-docker-test busybox:latest true")
    assert docker.container_stop('xd-docker-test') == False


def test_no_such_container(docker, stdout):
    with pytest.raises(ClientError) as clienterror:
        with stdout.redirect():
            docker.container_stop('xd-docker-test')
    assert clienterror.value.code == 404
