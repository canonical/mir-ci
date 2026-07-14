# mir-ci

`mir-ci` contains integration tests for Mir-based projects, covering specific
applications, output scaling, on-screen keyboards, drag and drop, and more.

The projects tested are:

- [Ubuntu Frame](https://github.com/canonical/ubuntu-frame)
- [Mir Test Tools](https://github.com/canonical/mir-test-tools)
- [Mir Demo Server](https://github.com/canonical/mir/tree/main/examples/mir_demo_server)
- Confined Shell
- [Miriway](https://github.com/Miriway/Miriway)
- [Mir Kiosk](https://snapcraft.io/mir-kiosk)

## Running the tests

The recommended way to run `mir-ci` is inside a
[Workshop](https://ubuntu.com/workshop/docs/) container, which wraps the project
and its dependencies into an LXD container. A ready-made
[`workshop.yaml`](./workshop.yaml) is included.

### Install Workshop

Workshop needs LXD 6.8+:

```sh
sudo snap install --channel=6/stable lxd
sudo snap install --classic workshop
```

### Launch the workshop

```sh
git clone https://github.com/canonical/mir-ci
cd mir-ci
workshop launch
```

This creates an Ubuntu 26.04 container with the project bind-mounted at
`/project` and builds the virtual environment automatically.

Install any dependencies not pre-seeded in the image with the `deps` action
(re-run it after adding a test that needs new dependencies):

```sh
workshop run mir-ci -- deps                  # all tests
workshop run mir-ci -- deps -k ubuntu_frame  # a subset
```

> [!NOTE]
> The server and application snaps are pre-seeded and wired up in the image, so
> the tests they back run without a separate `deps` step. A snap that can't be
> installed headless (e.g. `mir-kiosk`, which needs a VT) is skipped. The
> environment uses a uv-managed Python 3.12, as some suites need `rpaframework`,
> which doesn't support the Python 3.14 in Ubuntu 26.04.

### Run the tests

The `test` action runs the suite inside Xvfb; extra arguments are forwarded to
`pytest`:

```sh
workshop run mir-ci -- test                          # everything
workshop run mir-ci -- test -k ubuntu_frame           # one suite
workshop run mir-ci -- test -k "ubuntu_frame or miriway"
workshop run mir-ci -- test --junitxml=junit.xml
```

Other actions:

```sh
workshop run mir-ci -- list        # collect tests without running them
workshop run mir-ci -- self-test   # the suite's own self tests
workshop run mir-ci -- lint        # pre-commit static analysis
```

Use `workshop shell` for an interactive shell in the container.

## Debug runs in GitHub Actions

1. Restart a failing run with "Enable debug logging" checked.
1. Wait for a step to fail.
1. Find the tmate connection details in the job logs:
   ```sh
   Web shell: https://tmate.io/t/...
   SSH: ssh ...@xxx.tmate.io
   ```
