#!/bin/bash

if [ "$TRAVIS" = "true" ] ; then
    # Use Travis CI provided Python runtime on travis-ci.org
    PYTEST="py.test"
    export PYTHONPATH=`pwd`
else
    # Build our own Python runtime based on official Python docker image
    python_version=${PYTHON_VERSION-3.5}
    cat tests/unit/Dockerfile | \
    sed -e "s/\(FROM python\):.*/\1:${python_version}/" \
	> tests/unit/Dockerfile.tmp
    docker build -t xd-docker-unit-test -f tests/unit/Dockerfile.tmp .
    rm tests/unit/Dockerfile.tmp
    PYTEST="docker run --rm -v $PWD:/src -w /src -e PYTHONPATH=/src \
       xd-docker-unit-test py.test"
fi

# Default py.test arguments
if [ $# -eq 0 ] ; then
    PYTEST+=" tests/unit"
elif [[ "$1" == -* ]] ; then
    PYTEST+=" tests/unit $*"
else
    PYTEST+=" $*"
fi

set -ex

$PYTEST --cov=xd.docker
