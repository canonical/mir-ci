import shutil
import subprocess

from typing import Optional

import pytest

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
                subprocess.check_call(['sudo', 'apt-get', 'install', '--yes', *debs])
            if snap is not None:
                subprocess.check_call(('sudo', 'snap', 'install', snap, '--channel', channel))
                if shutil.which(f'/snap/{snap}/current/bin/setup.sh'):
                    subprocess.check_call(('sudo', f'/snap/{snap}/current/bin/setup.sh'))
    return cmd
