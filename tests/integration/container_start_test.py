import pytest
import os
import re

from xd.docker.client import *


def test_ok(docker, stdout):
    os.system("docker create --name xd-docker-test busybox:latest echo test")
    assert docker.container_start('xd-docker-test') == True

    
def test_no_such_container(docker, stdout):
    with pytest.raises(ClientError) as clienterror:
        with stdout.redirect():
            docker.container_start('xd-docker-test')
    assert clienterror.value.code == 404

    
def test_container_running(docker, stdout):
    os.system("docker run -d --name xd-docker-test busybox:latest sleep 600")
    assert docker.container_start('xd-docker-test') == False
