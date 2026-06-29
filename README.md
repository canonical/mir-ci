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

## Running the tests
The recommended way to run `mir-ci` is inside a [Workshop](https://ubuntu.com/workshop/docs/)
container. Workshop is a Canonical tool that wraps a project and its
dependencies into an LXD container, so anyone can run `mir-ci` without
installing anything on their host. A ready-made [`workshop.yaml`](./workshop.yaml)
is included at the root of this repository.

> [!TIP]
> Prefer to run the tests directly on your host instead? See
> [Running mir-ci on your local setup](./docs/running-locally.md).

### Install Workshop
Workshop relies on LXD 6.8+:

```sh
sudo snap install --channel=6/stable lxd
sudo snap install --classic workshop
```

### Launch the workshop
From the root of a checkout of this repository:

```sh
git clone https://github.com/canonical/mir-ci
cd mir-ci

workshop launch
```

This creates an Ubuntu 26.04 container with the project bind-mounted at
`/project`. Next, install a supported Python (via pyenv), the `mir_ci`
package, and its test harness:

```sh
workshop run mir-ci -- setup
```

### Install the test dependencies
Install the dependencies (snaps, debs, and pip packages) for the tests you are
interested in. To install everything:

```sh
workshop run mir-ci -- deps
```

To install dependencies for a specific test, forward a pytest selector:

```sh
workshop run mir-ci -- deps -k ubuntu_frame
```

> [!NOTE]
> The first `setup` run builds Python 3.12 with pyenv (a few minutes), because
> some suites depend on `rpaframework`, which does not yet support the Python
> 3.14 that ships in Ubuntu 26.04.

### Run the tests
The `test` action runs the suite inside a virtual X11 server. With no selector
it runs every suite Any extra arguments are forwarded straight to `pytest`:

```sh
# Run everything
workshop run mir-ci -- test

# Run a specific test suite
workshop run mir-ci -- test -k ubuntu_frame

# Run multiple test suites
workshop run mir-ci -- test -k "ubuntu_frame or miriway"

# Record test properties
workshop run mir-ci -- test --junitxml=junit.xml
```

Other convenience actions are available:

```sh
workshop run mir-ci -- list        # collect the available tests without running them
workshop run mir-ci -- list -m smoke   # limit collection to a marker
workshop run mir-ci -- self-test   # run the test suite's own self tests
workshop run mir-ci -- lint        # run the pre-commit static analysis
```

To get an interactive shell inside the container, run `workshop shell`. From
there you can work directly with the project at `/project/mir-ci/mir_ci`, as
described in [Running mir-ci on your local setup](./docs/running-locally.md).

## Debug runs in GitHub Actions
1. Restart a failing run, checking the "Enable debug logging" box
2. Wait for any step to fail
3. Find the tmate connection details in the job logs:
   ```sh
   Web shell: https://tmate.io/t/...
   SSH: ssh ...@xxx.tmate.io
   ```
