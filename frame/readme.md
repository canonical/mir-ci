# Ubuntu Frame Integration Tests

## To run
`pytest`

To run inside of a virtual X11 server:
`xvfb-run -a pytest`

To only run tests for a specific server, use `-k EXPRESSION`:
`xvfb-run -a pytest -k ubuntu-frame`

To run tests for some but not all servers, you can use logical expressions:
`xvfb-run -a pytest -k 'ubuntu-frame or mir-kiosk'`

To record test properties:
`xvfb-run -a pytest --junitxml=junit.xml`

## To typecheck tests
(this is also run as part of the test suite)
`mypy .`
