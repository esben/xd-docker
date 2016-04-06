#!/bin/bash

suite="$1"
shift
case "$suite" in

    unit)
	pip install -r tests/requirements.txt
	`dirname $0`/unit-test.sh --cov-report=xml
	;;

    integration)
	pip install -r tests/requirements.txt
	`dirname $0`/integration-test.sh --cov-report=xml
	;;

    style)
	pip install flake8
	flake8 --show-source --statistics --count xd/docker
	;;

    *)
	echo "Unknown test suite: $suite"
	exit 1
	;;

esac
