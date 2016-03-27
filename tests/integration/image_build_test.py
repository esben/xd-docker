import pytest
import contextlib
import os
import re

from xd.docker.client import *


@pytest.fixture
def busybox_hello(cleandir):
    with open('Dockerfile', 'w') as dockerfile:
        dockerfile.write('''\
FROM busybox
RUN echo Hello world
''')
    return cleandir


@pytest.fixture
def busybox_error(cleandir):
    with open('Dockerfile', 'w') as dockerfile:
        dockerfile.write('''\
FROM busybox
RUN false
''')
    return cleandir
    

def test_image_build_1_pull(docker, busybox_hello, stdout):
    with stdout.redirect():
        image = docker.image_build('.', pull=True)
    assert image is not None
    assert re.search('^Pulling .*busybox$', stdout.get(), re.M)


def test_image_build_2_nocache(docker, busybox_hello, stdout):
    with stdout.redirect():
        image = docker.image_build('.', cache=False)
    assert image is not None
    assert re.search('^Hello world$', stdout.get(), re.M)
    assert not re.search('^ ---> Using cache$', stdout.get(), re.M)

    
def test_image_build_3_cached(docker, busybox_hello, stdout):
    docker.image_build('.')
    with stdout.redirect():
        image = docker.image_build('.')
    assert image is not None
    assert re.search('^ ---> Using cache$', stdout.get(), re.M)
    assert not re.search('^Hello world$', stdout.get(), re.M)

        
def test_image_build_4_norm(docker, busybox_hello, stdout):
    with stdout.redirect():
        image = docker.image_build('.', cache=False, rm=False)
    assert image is not None
    assert not re.search('^Removing intermediate container', stdout.get(), re.M)

    
def test_image_build_5_forcerm(docker, busybox_hello, stdout):
    with stdout.redirect():
        image = docker.image_build('.', cache=False, force_rm=True)
    assert image is not None
    assert re.search('^Removing intermediate container', stdout.get(), re.M)


def test_image_build_6_alt_dockerfile(docker, busybox_hello, stdout):
    os.rename('Dockerfile', 'DockerfileX')
    with stdout.redirect():
        image = docker.image_build('.', dockerfile='DockerfileX')
    assert image is not None


def test_image_build_7_context_as_file(docker, busybox_hello, stdout):
    with stdout.redirect():
        image = docker.image_build('Dockerfile')
    assert image is not None


def test_image_build_8_and_tag(docker, busybox_hello, stdout):
    with stdout.redirect():
        image = docker.image_build('.', tag='xd-docker-unittest')
    assert image is not None

    
def test_image_build_9_error(docker, busybox_error, stdout):
    with stdout.redirect():
        image = docker.image_build('.', cache=False)
    assert image is None
    assert re.search(
        '^The command ./bin/sh -c false. returned a non-zero code: 1$',
        stdout.get(), re.M)


def test_image_build_10_error_quiet(docker, busybox_error, stdout):
    with stdout.redirect():
        image = docker.image_build('.', cache=False, output=('error'))
    assert image is None
    assert re.search(
        '^The command ./bin/sh -c false. returned a non-zero code: 1$',
        stdout.get(), re.M)
    assert len(stdout.getlines()) == 1
