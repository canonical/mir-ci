# Ubuntu Frame Integration Tests

## To select a subset of tests
This applies to any use of `pytest` below. To select a subset of tests,
use `-k EXPRESSION`, replacing hyphens with underscores:

`-k ubuntu_frame`

You can use logical expressions:

`-k ubuntu_frame or mir_demo_server`

See more:
https://docs.pytest.org/en/latest/how-to/usage.html#specifying-which-tests-to-run

## To install dependencies
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

## To typecheck tests
(this is also run as part of the test suite)
`mypy .`
