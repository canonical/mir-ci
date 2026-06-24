# mir-ci
`mir-ci` contains integration tests for different Mir-based projects.
These tests include specific applications, output scaling, on-screen
keyboards, drag and drop, and more.

The projects tested are:

- [Ubuntu Frame](https://github.com/canonical/ubuntu-frame)
- [Mir Test Tools](https://github.com/canonical/mir-test-tools)
- [Mir Demo Server](https://github.com/canonical/mir/tree/main/examples/mir_demo_server)
- Confined Shell
- [Miriway](https://github.com/Miriway/Miriway)
- [Mir Kiosk](https://snapcraft.io/mir-kiosk)

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

## Running Tests
> [!IMPORTANT]  
> These tests require a session that is NOT currently running any graphical session.
> Make sure that you are logged out of the desktop session before running the tests.

> [!WARNING]
> The Mir-based servers need DRM master to drive a real display, and the kernel only
> grants this to the process owning the **active virtual terminal (VT)**. A remote SSH
> or `tty` login runs on a pseudo-terminal, which is not a VT, so the servers fail to
> start with errors like `Failed to acquire DRM master: Operation not permitted` and
> `Failed to find any platforms for current system`.
>
> To run against a real display, log in on a physical VT (e.g. Ctrl+Alt+F3) with the
> desktop session logged out. To run headless or over SSH, use the virtual X11 server
> (`xvfb-run -a pytest`, see below), which renders via Mir's X11 platform and never
> touches DRM/KMS.

To run all tests, execute pytest. Note that this will take over your entire graphical
session while it runs, and it will take a long time:

```sh
source venv/bin/activate  # Always source the virtual environment first
pytest
```

You can also run a specific test suite with:

```sh
pytest -k <test_suite>

# Or run multiple test suites with:
pytest -k <test_suite_a> or <test_suite_b>
```

To run inside of a virtual X11 server:
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

## Debug runs in GitHub Actions
1. Restart a failing run, checking the "Enable debug logging" box
2. Wait for any step to fail
3. Find the tmate connection details in the job logs:
   ```sh
   Web shell: https://tmate.io/t/...
   SSH: ssh ...@xxx.tmate.io
   ```
