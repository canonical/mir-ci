# Running mir-ci on your local setup

> [!NOTE]
> The recommended way to run `mir-ci` is inside a [Workshop](https://ubuntu.com/workshop/docs/)
> container — see the [README](../README.md) for the quick start. This document
> is for contributors who would rather run the tests directly on their host.

## Setup
Install the dependencies and set up the virtual environment:

```sh
git clone https://github.com/canonical/mir-ci
cd mir-ci/mir-ci/mir_ci

python3 -m venv venv
source venv/bin/activate
pip install -e ..
```

Next, install the test environment for the tests that you are interested in. To
install all of the test dependencies, run:

```sh
pytest --deps
```

To install dependencies for a specific test, run:

```sh
pytest -k <test_name> --deps
```

A test suite will FAIL if the dependencies are not installed.


## Listing available tests
To discover all available tests without running them, use pytest's
collection mode:

```sh
pytest --collect-only

# For a compact list of test IDs:
pytest --collect-only -q
```

You can also limit collection to a specific marker (e.g. `smoke`,
`performance`, or `self`):

```sh
pytest --collect-only -m smoke
```

## Running
To run the tests from a VT or SSH session on **real hardware**, run:

```sh
source venv/bin/activate  # Always source the virtual environment first
pytest
```

You can also run a specific test suite with:

```sh
pytest -k <test_suite>

# Or run multiple test suites with:
pytest -k "<test_suite_a> or <test_suite_b>"
```

For example, to run the `ubuntu_frame` test suite:

```sh
pytest -k ubuntu_frame
```

To run inside of a virtual **X11 server**, run:
```sh
sudo apt install xvfb
xvfb-run -a pytest
```

To record test properties:
```sh
xvfb-run -a pytest --junitxml=junit.xml
```

### Self Tests
Because it is a complex piece of software, we have tests for the test suite itself.
You can run those tests with:

```sh
pytest -m self
```

## Static Analysis
The `pre-commit` tool is used for static analysis.

```sh
pip install pre-commit
pre-commit run

# To run before each commit:
pre-commit install
```
