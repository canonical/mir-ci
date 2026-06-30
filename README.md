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
`/project`. The virtual environment and the `mir_ci` package are built
automatically as part of `workshop launch`, so no manual setup step is needed.

Before running the tests, install any dependencies that are not already part of
the container image (e.g. Python packages, or snaps/debs for tests that aren't
pre-seeded) with the `deps` action:

```sh
# Install the dependencies for all tests
workshop run mir-ci -- deps

# Or limit the dependencies to the tests you are interested in
workshop run mir-ci -- deps -k ubuntu_frame
```

Run `deps` again whenever you add or change a test that needs new dependencies.

> [!NOTE]
> The server and application snaps (and the common app debs) are pre-seeded
> *and* wired up (their `setup.sh`, `wayland` and `login-session-control`
> interfaces) when the container image is built, so the tests they back can be
> run straight away without a separate `deps` step. A snap that cannot be
> installed in a headless container (e.g. `mir-kiosk`, which needs a VT) is
> skipped.

> [!NOTE]
> The environment uses a uv-managed Python 3.12, because some suites depend on
> `rpaframework`, which does not yet support the Python 3.14 that ships in
> Ubuntu 26.04. uv downloads a prebuilt CPython, so nothing is compiled.

### Run the tests
The `test` action runs the suite inside a virtual X11 server (Xvfb). With no
selector it runs every suite. Any extra arguments are forwarded straight to
`pytest`:

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
