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

> [!IMPORTANT]
> These are graphics/hardware integration tests that Canonical runs on real lab
> devices. A headless LXD container reliably runs the subset that does not need
> hardware acceleration, a seat/session, or per-app cgroup CPU accounting (server
> startup, app launches that don't crash on software rendering, and the harness'
> own self tests). Suites that exercise the screencopy/scaling pipeline,
> on-screen keyboard, drag-and-drop, VNC, or GPU-accelerated apps are expected to
> fail in a plain container because:
> - the container has no GPU by default (LXD does not pass one through, and even
>   a manually attached GPU needs a Mesa build that matches the host hardware);
> - the `wlr-screencopy` client path used by those tests cannot complete its
>   `wl_shm` buffer hand-off under purely software rendering;
> - per-app CPU metrics need a delegated `cpu` cgroup controller, and some apps
>   (e.g. `qterminal`) crash under software rendering.
>
> The `gnome_shell` suite runs headless in the container: when it detects it is
> nested inside an existing X11 or Wayland session (as it is under Xvfb here),
> the fixture launches GNOME Shell with `--headless --virtual-monitor`, the same
> way GNOME's own CI does, so it does not need a logind seat or a VT. On real
> hardware with a seat it still uses mutter's native backend.
>
> These limitations are environmental, not a fault of the `workshop.yaml` setup:
> dependency installation, the compositors, and the test harness all work, and
> the headless-capable tests pass. Run the full suite on real hardware (see
> [Running mir-ci on your local setup](./docs/running-locally.md)) for complete
> coverage.

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
