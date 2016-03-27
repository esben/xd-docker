import pytest
import contextlib
import re

from xd.docker.client import *
    

def test_image_pull_1_ok(docker, stdout):
    with stdout.redirect():
        assert docker.image_pull('busybox:latest')
    assert re.match('Status: (Image is up to date|Downloaded newer image)',
                    stdout.lastline())

def test_image_pull_2_not_found(docker, stdout):
    with stdout.redirect():
        assert not docker.image_pull('nosuchthingshouldexist', output=('error'))
    assert re.search('nosuchthingshouldexist.* not found', stdout.lastline())

def test_image_pull_3_invalid_registry_auth(docker):
    with pytest.raises(TypeError):
        docker.image_pull('busybox:latest', registry_auth=42)
