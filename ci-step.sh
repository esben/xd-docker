#!/bin/bash

suite="$1"
shift
case "$suite" in

    unit)
	`dirname $0`/unit-test.sh
	;;

    integration)
	`dirname $0`/integration-test.sh
	;;

    style)
	flake8 --show-source --statistics --count xd/docker
	;;

    doc)
	./docs/make.sh
	;;

    *)
	echo "Unknown test suite: $suite"
	exit 1
	;;

esac
