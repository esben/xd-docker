#!/bin/bash

suite="$1"
shift
case "$suite" in

    unit)
	`dirname $0`/unit-test.sh --cov-report=xml
	;;

    integration)
	`dirname $0`/integration-test.sh --cov-report=xml
	;;

    style)
	flake8 --show-source --statistics --count xd/docker
	;;

    manifest)
	pip install check-manifest
	check-manifest
	;;

    *)
	echo "Unknown test suite: $suite"
	exit 1
	;;

esac
