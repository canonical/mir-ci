# Running mir-ci on your local setup

> [!NOTE]
> The recommended way to run `mir-ci` is inside a
> [Workshop](https://ubuntu.com/workshop/docs/) container — see the
> [README](../README.md). This document is for running the tests directly on
> your host.

## Setup
```sh
git clone https://github.com/canonical/mir-ci
cd mir-ci/mir-ci/mir_ci

python3 -m venv venv
source venv/bin/activate
pip install -e ..
```

Install the test dependencies (a suite FAILs if its dependencies are missing):

```sh
pytest --deps              # all tests
pytest -k <test_name> --deps  # a specific test
```

## Listing tests
```sh
pytest --collect-only -q       # compact list of test IDs
pytest --collect-only -m smoke  # limit to a marker
```

## Running
Always source the virtual environment first. On **real hardware** (from a VT or
SSH session):

```sh
source venv/bin/activate
pytest
pytest -k ubuntu_frame                       # one suite
pytest -k "<test_suite_a> or <test_suite_b>"  # multiple
```

Inside a virtual **X11 server**:

```sh
sudo apt install xvfb
xvfb-run -a pytest
xvfb-run -a pytest --junitxml=junit.xml  # record test properties
```

### Self tests
The suite has tests for itself:

```sh
pytest -m self
```

## Static analysis
```sh
pip install pre-commit
pre-commit run
pre-commit install  # run before each commit
```
