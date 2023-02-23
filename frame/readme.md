# Ubuntu Frame Integration Tests

## To run
`python3 -m unittest`

To run inside of a virtual X11 server:
`xvfb-run python3 -m unittest`

To only run tests for a specific server, set `MIR_TEST_SERVER`:
`MIR_TEST_SERVER=ubuntu-frame xvfb-run python3 -m unittest`

To to run tests for some but not all servers a list can be specified:
`MIR_TEST_SERVER=ubuntu-frame,mir-kiosk xvfb-run python3 -m unittest`

## To typecheck tests
(this is also run as part of the test suite)
`mypy .`
