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
Just add `--install` to your test invocation. There's a dummy `deps.py` test module
if you don't want to also run the tests:
`pytest --install deps.py`
`pytest -k confined_shell --install deps.py`
`pytest -k confined_shell --install`

## To run
`pytest`
`pytest -k mir_kiosk install_deps.py`

To run inside of a virtual X11 server:
`xvfb-run -a pytest`

To record test properties:
`xvfb-run -a pytest --junitxml=junit.xml`

## To typecheck tests
(this is also run as part of the test suite)
`mypy .`
