#!/bin/bash

# Allow specifying alternative docker versions
daemon_version=${DOCKER_VERSION-1.10}
client_version=${DOCKER_CLIENT_VERSION-${daemon_version}}

# Setup py.test runner command, using dind and client docker cointainers
PYTEST="docker run --rm --link xd-docker-dind:docker \
    -v $PWD:/src -w /src -e PYTHONPATH=/src \
    -e DOCKER_HOST=tcp://docker:2375 \
    xd-docker-integration-test \
    py.test"

# Default py.test arguments
if [ $# -eq 0 ] ; then
    PYTEST+=" tests/integration"
elif [[ "$1" == -* ]] ; then
    PYTEST+=" tests/integration $*"
else
    PYTEST+=" $*"
fi

set -ex

# Start new docker-in-docker container
if docker inspect --type container xd-docker-dind >/dev/null 2>/dev/null ; then
    docker rm -f xd-docker-dind
fi
docker run -d --privileged --name xd-docker-dind docker:${daemon_version}-dind

# Build docker client image
cat tests/integration/Dockerfile | \
    sed -e "s/\(FROM docker\):.*/\1:${client_version}/" \
	> tests/integration/Dockerfile.tmp
docker build -t xd-docker-integration-test -f tests/integration/Dockerfile.tmp .
rm tests/integration/Dockerfile.tmp
$PYTEST --cov=xd.docker --cov-report=term-missing --cov-report=xml
