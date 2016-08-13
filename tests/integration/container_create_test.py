import pytest
import contextlib
import os
import re

from xd.docker.client import *
from xd.docker.container import *
from xd.docker.parameters import *


def test_pull_needed(docker, stdout):
    with stdout.redirect():
        container = docker.container_create(
            ContainerConfig("busybox:latest"),
            "xd-docker-container-create-1")
    assert container is not None
    assert isinstance(container, Container)
    assert re.match('^[0-9a-f]+$', container.id)


def test_pull_but_not_needed(docker, stdout):
    docker.image_pull("busybox:latest")
    with stdout.redirect():
        container = docker.container_create(
            ContainerConfig("busybox:latest"),
            "xd-docker-container-create-2")
    assert container is not None
    assert isinstance(container, Container)
    assert re.match('^[0-9a-f]+$', container.id)


def test_no_pull_but_needed(docker, stdout):
    with pytest.raises(ClientError):
        docker.container_create(
            ContainerConfig("busybox:latest"),
            "xd-docker-container-create-3",
            pull=False)


def test_no_pull_and_not_needed(docker, stdout):
    docker.image_pull("busybox:latest")
    with stdout.redirect():
        container = docker.container_create(
            ContainerConfig("busybox:latest"),
            "xd-docker-container-create-4",
            pull=False)
    assert container is not None
    assert isinstance(container, Container)
    assert re.match('^[0-9a-f]+$', container.id)
