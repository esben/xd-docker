XD Docker
=========

XD Docker client wrapper for Python 3.

The goal is to provide a functional, easy to use and Pythonic API for working
with Docker in Python.

## License

XD Docker is released under the MIT License (see LICENSE file).

## Test suites

XD Docker includes both a unit test suite and an integration test suite.

The goal of the unit test suite is to test each module, achieving 100% code
and branch coverage.

The goal of the integration test suite is to test against different docker
versions.

The recommended way to run the test suites, is to use the shell scripts
`unit-test.sh` and `integration-test.sh`.

These scripts take care of building docker images with the necessary tools and
software, and runs the test in docker containers.
