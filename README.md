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

These tests are run in Canonical's lab across many different devices. The results
of these runs are displayed on an internal dashboard for security reasons.

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

> [!WARNING]
> I have noticed that the `--deps` installer may install older versions of
> certain snaps (e.g. Ubuntu Frame). Unfortunately, these versions may not be compatible
> with the hardware that your computer is running. It is advised that if a test fails to
> run, you should try to install a later version of its dependencies manually.
>
> For example, frame 24 can be installed with:
> ```sh
> sudo snap install ubuntu-frame --channel=24
> ```

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
pytest -k <test_suite_a> or <test_suite_b>
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

## Debug runs in GitHub Actions
1. Restart a failing run, checking the "Enable debug logging" box
2. Wait for any step to fail
3. Find the tmate connection details in the job logs:
   ```sh
   Web shell: https://tmate.io/t/...
   SSH: ssh ...@xxx.tmate.io
   ```
