import platform
import shutil
import subprocess

from typing import Optional

import pytest

RELEASE_PPA = 'mir-team/release'
RELEASE_PPA_ENTRY = f'https://ppa.launchpadcontent.net/{RELEASE_PPA}/ubuntu {platform.freedesktop_os_release()["VERSION_CODENAME"]}/main'
APT_INSTALL = ('sudo', 'DEBIAN_FRONTEND=noninteractive', 'apt-get', 'install', '--yes')

@pytest.fixture(scope='session')
def ppa() -> None:
    if RELEASE_PPA_ENTRY not in subprocess.check_output(('apt-cache', 'policy')).decode():
        subprocess.check_call((*APT_INSTALL, 'software-properties-common'))
        subprocess.check_call(('sudo', 'add-apt-repository', '--yes', f'ppa:{RELEASE_PPA}'))

@pytest.fixture(scope='module', params=(
    pytest.param('ubuntu-frame', id='ubuntu_frame'),
    pytest.param('mir-kiosk', id='mir_kiosk'),
    pytest.param({'snap': 'confined-shell', 'channel': 'edge'}, id='confined_shell'),
    pytest.param({'cmd': 'mir_demo_server', 'debs': ('mir-test-tools', 'mir-graphics-drivers-desktop')}, id='mir_demo_server'),
))
def server(request: pytest.FixtureRequest) -> str:
    install: bool = getattr(request.module, 'install', False)
    if isinstance(request.param, dict):
        cmd: str = request.param.get('cmd', request.param.get('snap'))
        debs: Optional[tuple[str]] = request.param.get('debs')
        snap: Optional[str] = request.param.get('snap')
        channel: str = request.param.get('channel', 'latest/stable')
    else:
        cmd = request.param
        debs = None
        snap = request.param
        channel = 'latest/stable'

    if shutil.which(cmd) is None:
        if not install:
            pytest.skip(f'server executable not found: {cmd}')
        else:
            if debs is not None:
                request.getfixturevalue('ppa')
                subprocess.check_call((*APT_INSTALL, *debs))
            if snap is not None:
                subprocess.check_call(('sudo', 'snap', 'install', snap, '--channel', channel))
                if shutil.which(f'/snap/{snap}/current/bin/setup.sh'):
                    subprocess.check_call(('sudo', f'/snap/{snap}/current/bin/setup.sh'))
    return cmd
