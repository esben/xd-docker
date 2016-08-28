import pytest
import os

from xd.docker.client import *


def test_kill(docker, stdout):
    os.system("docker run -d --name xd-docker-test busybox:latest sleep 10")
    docker.container_kill('xd-docker-test')


def test_already_stopped(docker, stdout):
    os.system("docker run --name xd-docker-test busybox:latest true")
    # Prior to Docker 1.8, kill silently ignores stopped containers, and
    # beginning with 1.8, they return HTTP 500 (ServerError)
    if docker.api_version > (1, 19):
        with pytest.raises(ServerError) as servererror:
            docker.container_kill('xd-docker-test')
    else:
        docker.container_kill('xd-docker-test')


def test_not_started(docker, stdout):
    os.system("docker create --name xd-docker-test busybox:latest true")
    # Prior to Docker 1.8, kill silently ignores stopped containers, and
    # beginning with 1.8, they return HTTP 500 (ServerError)
    if docker.api_version > (1, 19):
        with pytest.raises(ServerError) as servererror:
            docker.container_kill('xd-docker-test')
    else:
        docker.container_kill('xd-docker-test')


def test_no_such_container(docker, stdout):
    with pytest.raises(ClientError) as clienterror:
        with stdout.redirect():
            docker.container_kill('xd-docker-test')
        assert clienterror.value.code == 404
