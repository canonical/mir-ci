from display_server import DisplayServer
from screencopy_tracker import ScreencopyTracker
import pytest
import os
import re
import asyncio

import apps

long_wait_time = 10

ASCIINEMA_CAST = f'{os.path.dirname(__file__)}/data/demo.cast'
SERVER_MODE_RE = re.compile(r'Current mode ([0-9x]+ [0-9.]+Hz)')
SERVER_RENDERER_RE = re.compile(r'GL renderer: (.*)$', re.MULTILINE)

def _record_properties(fixture, server, tracker):
    for name, val in tracker.properties().items():
        fixture(name, val)
    fixture('server_mode', SERVER_MODE_RE.search(server.server.output).group(1))
    fixture('server_renderer', SERVER_RENDERER_RE.search(server.server.output).group(1))

@pytest.mark.performance
class TestScreencopyBandwidth:
    @pytest.mark.parametrize('app', [
        apps.qterminal('--execute', f'python3 -m asciinema play {ASCIINEMA_CAST}', pip_pkgs=('asciinema',), id='asciinema', extra=15),
        apps.snap('mir-kiosk-neverputt', extra=False)
    ])
    async def test_active_app(self, record_property, server, app) -> None:
        server = DisplayServer(server, add_extensions=ScreencopyTracker.required_extensions)
        tracker = ScreencopyTracker(server.display_name)
        with server as s, tracker, s.program(app[0]) as p:
            if app[1]:
                p.wait(app[1])
            else:
                await asyncio.sleep(long_wait_time)
        _record_properties(record_property, server, tracker)

    async def test_compositor_alone(self, record_property, server) -> None:
        server = DisplayServer(server, add_extensions=ScreencopyTracker.required_extensions)
        tracker = ScreencopyTracker(server.display_name)
        with server, tracker:
            await asyncio.sleep(long_wait_time)
        _record_properties(record_property, server, tracker)

    @pytest.mark.parametrize('app', [
        apps.qterminal(),
        apps.gedit(),
        apps.snap('mir-kiosk-kodi'),
    ])
    async def test_inactive_app(self, record_property, server, app) -> None:
        server = DisplayServer(server, add_extensions=ScreencopyTracker.required_extensions)
        tracker = ScreencopyTracker(server.display_name)
        with server as s, tracker, s.program(app):
            await asyncio.sleep(long_wait_time)
        _record_properties(record_property, server, tracker)
