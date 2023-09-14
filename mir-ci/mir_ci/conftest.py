import pathlib
import shutil
import subprocess

from collections.abc import Iterator
from typing import Any, Generator, List, Mapping, Optional, Union

import distro
import pytest

from mir_ci import apps

RELEASE_PPA = 'mir-team/release'
RELEASE_PPA_ENTRY = f'https://ppa.launchpadcontent.net/{RELEASE_PPA}/ubuntu {distro.codename()}/main'
APT_INSTALL = ('sudo', 'DEBIAN_FRONTEND=noninteractive', 'apt-get', 'install', '--yes')
PIP = ('python3', '-m', 'pip')
DEP_FIXTURES = {'server', 'deps'}  # these are all the fixtures changing their behavior on `--deps`

def pytest_addoption(parser):
    parser.addoption(
        '--deps', help='Only install the test dependencies', action='store_true'
    )

def _find_pips(pips):
    missing = []
    for pkg in pips:
        try:
            __import__(isinstance(pkg, tuple) and pkg[1] or pkg)
        except ImportError:
            missing.append(isinstance(pkg, tuple) and pkg[0] or pkg)
    return missing

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

def _deps_install(request: pytest.FixtureRequest, spec: Union[str, Mapping[str, Any]]) -> List[str]:
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
        cmd: List[str] = spec.get('cmd', []) or [spec.get('snap')]
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
        raise TypeError('Bad value for argument `spec`: ' + repr(spec))

    if request.config.getoption("--deps", False):
        if debs:
            checked_debs = request.session.keywords.setdefault('debs', set())
            unchecked_debs = set(debs).difference(checked_debs)
            if unchecked_debs:
                try:
                    subprocess.check_call(('dpkg', '--status', *unchecked_debs),
                                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                except subprocess.CalledProcessError:
                    request.getfixturevalue('ppa')
                    subprocess.check_call((*APT_INSTALL, *unchecked_debs))
                checked_debs.update(unchecked_debs)
        if snap:
            checked_snaps = request.session.keywords.setdefault('snaps', set())
            if snap not in checked_snaps:
                try:
                    subprocess.check_call(('snap', 'list', snap),
                                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                except subprocess.CalledProcessError:
                    subprocess.check_call(('sudo', 'snap', 'install', snap, '--channel', channel))
                    if shutil.which(f'/snap/{snap}/current/bin/setup.sh'):
                        subprocess.check_call(('sudo', f'/snap/{snap}/current/bin/setup.sh'))
                    subprocess.call(('sudo', 'snap', 'connect', f'{snap}:login-session-control'),
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                checked_snaps.add(snap)

        missing_pkgs = _find_pips(pip_pkgs)
        if missing_pkgs:
            subprocess.check_call((*PIP, 'install', *missing_pkgs))

        _deps_skip(request)

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
    apps.ubuntu_frame,
    apps.mir_kiosk,
    apps.confined_shell,
    apps.mir_test_tools,
    apps.mir_demo_server,
))
def server(request: pytest.FixtureRequest) -> List[str]:
    '''
    Parameterizes the servers (ubuntu-frame, mir-kiosk, confined-shell, mir_demo_server),
    or installs them if `--deps` is given on the command line.
    '''
    # Have to evaluate the param ourselves, because you can't mark fixtures and so
    # the `.deps(…)` mark never registers.
    return _deps_install(request, request.param().marks[0].kwargs)

@pytest.fixture(scope='function')
def deps(request: pytest.FixtureRequest) -> List[str]:
    '''
    Ensures the dependenciesa are available, or installs them if `--deps` is given on the command line.

    You need to provide data through the `deps` mark:
    ```
    @pytest.mark.deps('snap')                                   # where `snap` is the snap name and executable
    @pytest.mark.deps('snap', snap='the-snap', channel='edge')  # where `snap` is the executable
    @pytest.mark.deps('app', debs=('deb-one', 'deb-two'))       # where `app` is the executable
    @pytest.mark.deps('other-app', cmd=('the-app', 'arg'))      # `the-app` is the executable
    @pytest.mark.deps(pip_pkgs=('one','two'))                   # no executable, `one` and `two` installed with `pip`
    @pytest.mark.deps(pip_pkgs=(('pkg', 'module'),))            # `module` import checked, `pkg` installed with `pip`
    ```
    '''
    marks: Iterator[pytest.Mark] = request.node.iter_markers('deps')
    try:
        closest: pytest.Mark = next(marks)
    except StopIteration:
        _deps_skip(request)
        return []

    for mark in request.node.iter_markers('deps'):
        _deps_install(request, mark.kwargs and dict({'cmd': mark.args}, **mark.kwargs) or mark.args[0])

    return _deps_install(request, closest.kwargs and dict({'cmd': closest.args}, **closest.kwargs) or closest.args[0])

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
