import pathlib
import platform
import shutil
import subprocess

from collections.abc import Iterator
from typing import Any, Generator, Mapping, Optional, Union

import pytest

RELEASE_PPA = 'mir-team/release'
RELEASE_PPA_ENTRY = f'https://ppa.launchpadcontent.net/{RELEASE_PPA}/ubuntu {platform.freedesktop_os_release()["VERSION_CODENAME"]}/main'
APT_INSTALL = ('sudo', 'DEBIAN_FRONTEND=noninteractive', 'apt-get', 'install', '--yes')
PIP = ('python3', '-m', 'pip')
DEP_FIXTURES = {'server', 'deps'}  # these are all the fixtures changing their behavior on `--deps`

def pytest_addoption(parser):
    parser.addoption(
        '--deps', help='Only install the test dependencies', action='store_true'
    )

def _deps_skip(request: pytest.FixtureRequest) -> None:
    '''
    Keep a record of fixtures affected by `--deps` and only skip the request
    if all of them were evaluated already.
    '''
    assert request.fixturename in DEP_FIXTURES, f'`{request.fixturename}` not in DEP_FIXTURES'
    assert request.scope == 'function', 'Dependency management only possible in `function` scope'
    if request.config.getoption('--deps', False):
        request.keywords.setdefault('depfixtures', set()).add(request.fixturename)
        if request.keywords['depfixtures'] == DEP_FIXTURES.intersection(request.fixturenames):
            pytest.skip('dependency-only run')

def _deps_install(request: pytest.FixtureRequest, spec: Union[str, Mapping[str, Any]]) -> list[str]:
    '''
    Install dependencies for the command spec provided. If `spec` is a string, it's assumed
    to be a snap and command name.

    If `spec` is a dictionary, the following keys are supported:
    `cmd: list[str]`: the command to run, optionally including arguments
    `debs: list[str]`: optional list of deb packages to install
    `snap: str`: optional snap to install
    `pip_pkgs: list[str]`: optional list of python packages to install
    `channel: str`: the channel to install the snap from, defaults to `latest/stable`
    '''
    if isinstance(spec, dict):
        cmd: list[str] = spec.get('cmd', []) or [spec.get('snap')]
        debs: Optional[tuple[str]] = spec.get('debs')
        snap: Optional[str] = spec.get('snap')
        channel: str = spec.get('channel', 'latest/stable')
        pip_pkgs: tuple[str, ...] = spec.get('pip_pkgs', ())
    elif isinstance(spec, str):
        cmd = [spec]
        debs = None
        snap = spec
        channel = 'latest/stable'
        pip_pkgs = ()
    else:
        raise TypeError('Bad value for argument `spec`')

    if request.config.getoption("--deps", False):
        missing_pkgs = []
        for pkg in pip_pkgs:
            try:
                __import__(pkg)
            except ImportError:
                missing_pkgs.append(pkg)
        if missing_pkgs:
            subprocess.check_call((*PIP, 'install', *missing_pkgs))

        if shutil.which(cmd[0]) is None:
            if debs is not None:
                request.getfixturevalue('ppa')
                subprocess.check_call((*APT_INSTALL, *debs))
            if snap is not None:
                subprocess.check_call(('sudo', 'snap', 'install', snap, '--channel', channel))
                if shutil.which(f'/snap/{snap}/current/bin/setup.sh'):
                    subprocess.check_call(('sudo', f'/snap/{snap}/current/bin/setup.sh'))
        _deps_skip(request)

    if shutil.which(cmd[0]) is None:
        pytest.skip(f'server executable not found: {cmd[0]}')

    for pkg in pip_pkgs:
        try:
            __import__(pkg)
        except ImportError:
            pytest.skip(f'PIP package not found: {pkg}')

    return cmd

@pytest.fixture(scope='session')
def ppa() -> None:
    '''
    Ensures the mir-test/release PPA is enabled.
    '''
    if RELEASE_PPA_ENTRY not in subprocess.check_output(('apt-cache', 'policy')).decode():
        subprocess.check_call((*APT_INSTALL, 'software-properties-common'))
        subprocess.check_call(('sudo', 'add-apt-repository', '--yes', f'ppa:{RELEASE_PPA}'))

@pytest.fixture(scope='function', params=(
    pytest.param({'snap': 'ubuntu-frame', 'channel': '22/stable'}, id='ubuntu_frame'),
    pytest.param('mir-kiosk', id='mir_kiosk'),
    pytest.param({'snap': 'confined-shell', 'channel': 'edge'}, id='confined_shell'),
    pytest.param({'snap': 'mir-test-tools', 'channel': '22/beta', 'cmd': ('mir-test-tools.demo-server',)}, id='mir_test_tools'),
    pytest.param({'cmd': ['mir_demo_server'], 'debs': ('mir-test-tools', 'mir-graphics-drivers-desktop')}, id='mir_demo_server'),
))
def server(request: pytest.FixtureRequest) -> list[str]:
    '''
    Parameterizes the servers (ubuntu-frame, mir-kiosk, confined-shell, mir_demo_server),
    or installs them if `--deps` is given on the command line.
    '''
    return _deps_install(request, request.param)

@pytest.fixture(scope='function')
def deps(request: pytest.FixtureRequest) -> list[str]:
    '''
    Ensures the dependenciesa are available, or installs them if `--deps` is given on the command line.

    You need to provide data through the `deps` mark:
    ```
    @pytest.mark.deps('snap')                                   # where `snap` is the snap name and executable
    @pytest.mark.deps('snap', snap='the-snap', channel='edge')  # where `snap` is the executable
    @pytest.mark.deps('app', debs=('deb-one', 'deb-two'))       # where `app` is the executable
    @pytest.mark.deps('other-app', cmd=('the-app', 'arg'))      # `the-app` is the executable
    @pytest.mark.deps('pkg', pip_pkgs=('one','two'))            # `pkg` is the executable
    ```
    '''
    marks: Iterator[pytest.Mark] = request.node.iter_markers('deps')
    try:
        closest: pytest.Mark = next(marks)
    except StopIteration:
        _deps_skip(request)
        return []

    for mark in request.node.iter_markers('deps'):
        _deps_install(request, mark.kwargs and { 'cmd': mark.args } | mark.kwargs or mark.args[0])

    return _deps_install(request, closest.kwargs and {'cmd': mark.args } | closest.kwargs or closest.args[0])

@pytest.fixture(scope='function')
def xdg(request: pytest.FixtureRequest, tmp_path: pathlib.Path) -> Generator:
    '''
    Create a temporary directory, set environment variable to the temporary path,
    and write contents to files within.

    Use the `xdg` mark to provide data, e.g.:
    @pytest.mark.xdg(XDG_CONFIG_HOME={'dir/file': 'contents'})
    '''
    if request.config.getoption('--deps'):
        yield
        return

    with pytest.MonkeyPatch.context() as m:
        for mark in request.node.iter_markers('xdg'):
            for var, files in mark.kwargs.items():
                var_path = tmp_path / var
                var_path.mkdir(exist_ok=True)
                m.setenv(var, str(var_path))
                for file, contents in files.items():
                    (var_path / file).parent.mkdir(exist_ok=True, parents=True)
                    with open(var_path / file, 'w') as f:
                        f.write(contents)
        yield
