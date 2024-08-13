# Ubuntu Frame Integration Tests A

**NB:** Your working directory needs to be `mir-ci/mir_ci` for this to work.

## To install the package and suite dependencies
`pip install -e ..`

## To select a subset of tests
This applies to any use of `pytest` below. To select a subset of tests,
use `-k EXPRESSION`, replacing hyphens with underscores:

`-k ubuntu_frame`

You can use logical expressions:

`-k ubuntu_frame or mir_demo_server`

See more:
https://docs.pytest.org/en/latest/how-to/usage.html#specifying-which-tests-to-run

## To install test dependencies
Just add `--deps` to your test invocation. It will install all the dependencies
for the selected tests, but skip them.
`pytest --deps`
`pytest -k confined_shell --deps`

## To run
`pytest`
`pytest -k mir_kiosk`

To run inside of a virtual X11 server:
`xvfb-run -a pytest`

To record test properties:
`xvfb-run -a pytest --junitxml=junit.xml`

## To run self-tests
This runs internal tests.
`pytest -m self`

## To run static check and linters
`pip install pre-commit`
`pre-commit run`

And to run it before each commit:
`pre-commit install`
