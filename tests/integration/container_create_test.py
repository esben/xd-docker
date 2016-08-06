import pytest
import contextlib
import os
import re

from xd.docker.client import *
from xd.docker.container import *
from xd.docker.parameters import *


@pytest.fixture
def docker_with_busybox(docker):
    docker.image_pull("busybox")
    return docker


def test_container_create_1(docker_with_busybox, stdout):
    with stdout.redirect():
        container = docker_with_busybox.container_create(
            ContainerConfig("busybox"),
            "xd-docker-container-create-1")
    assert container is not None
    assert isinstance(container, Container)
    assert re.match('^[0-9a-f]+$', container.id)
