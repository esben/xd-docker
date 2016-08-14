import pytest
import os
import re

from xd.docker.client import *


def test_ok(docker, stdout):
    os.system("docker create --name xd-docker-test busybox:latest")
    docker.container_remove('xd-docker-test')

    
def test_no_such_container(docker, stdout):
    with pytest.raises(ClientError) as clienterror:
        with stdout.redirect():
            docker.container_remove('xd-docker-test')
    assert clienterror.value.code == 404

    
def test_container_running(docker, stdout):
    os.system("docker run -d --name xd-docker-test busybox:latest sleep 600")
    with pytest.raises(ClientError) as clienterror:
        with stdout.redirect():
            docker.container_remove('xd-docker-test')
    assert clienterror.value.code == 409

    
def test_container_running_force_false(docker, stdout):
    os.system("docker run -d --name xd-docker-test busybox:latest sleep 600")
    with pytest.raises(ClientError) as clienterror:
        with stdout.redirect():
            docker.container_remove('xd-docker-test', force=False)
    assert clienterror.value.code == 409

    
def test_container_running_force(docker, stdout):
    os.system("docker run -d --name xd-docker-test busybox:latest sleep 600")
    docker.container_remove('xd-docker-test', force=True)
