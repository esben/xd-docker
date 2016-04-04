#!/bin/bash

if [ "$TRAVIS" = "true" ] ; then
    cd docs
    MAKE="make"
else
    # Run in docker
    cd `dirname $0`/..
    docker build -t xd-docker-docs -f docs/Dockerfile .
    MAKE="docker run -v $PWD:/src -w /src/docs xd-docker-docs make"
fi

# Default make arguments
if [ $# -eq 0 ] ; then
    MAKE+=" html"
fi

$MAKE $*
