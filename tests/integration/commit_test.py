import pytest
import os
import re
import json


from xd.docker.client import *


def test_basic(docker, stdout):
    os.system("docker create --name xd-docker-test busybox:latest")
    foo = docker.commit('xd-docker-test')
    assert foo.id
    assert os.system('docker inspect {}'.format(foo.id) +
                     '|grep \'"Comment": "foobar"\'') != 0
    assert os.system('docker inspect {}'.format(foo.id) +
                     '|grep \'"Author": "foobar"\'') != 0


def test_with_repo(docker, stdout):
    os.system("docker create --name xd-docker-test busybox:latest")
    foo = docker.commit('xd-docker-test', repo='foo')
    assert foo.id


def test_with_tag(docker, stdout):
    os.system("docker create --name xd-docker-test busybox:latest")
    foo = docker.commit('xd-docker-test', repo='foo:bar')
    assert foo.id


def test_comment(docker, stdout):
    os.system("docker create --name xd-docker-test busybox:latest")
    foo = docker.commit('xd-docker-test', comment='foobar')
    assert foo.id
    assert os.system('docker inspect {}'.format(foo.id) +
                     '|grep \'"Comment": "foobar"\'') == 0


def test_author(docker, stdout):
    os.system("docker create --name xd-docker-test busybox:latest")
    foo = docker.commit('xd-docker-test', author='foobar')
    assert foo.id
    assert os.system('docker inspect {}'.format(foo.id) +
                     '|grep \'"Author": "foobar"\'') == 0


def test_pause_true(docker, stdout):
    os.system("docker create --name xd-docker-test busybox:latest")
    foo = docker.commit('xd-docker-test', pause=True)
    assert foo.id


def test_pause_false(docker, stdout):
    os.system("docker create --name xd-docker-test busybox:latest")
    foo = docker.commit('xd-docker-test', pause=False)
    assert foo.id
