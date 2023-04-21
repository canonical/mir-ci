from display_server import DisplayServer
from pathlib import Path
import pytest
import os
import re
import asyncio
import apps

try:
    from screencopy_tracker import ScreencopyTracker
    from virtual_pointer import VirtualPointer, Button
except ModuleNotFoundError as e:
    pass

long_wait_time = 10

ASCIINEMA_CAST = f'{os.path.dirname(__file__)}/data/demo.cast'
SERVER_MODE_RE = re.compile(r'Current mode ([0-9x]+ [0-9.]+Hz)')
SERVER_RENDERER_RE = re.compile(r'GL renderer: (.*)$', re.MULTILINE)

def _record_properties(fixture, server, tracker, min_frames):
    for name, val in tracker.properties().items():
        fixture(name, val)
    fixture('server_mode', SERVER_MODE_RE.search(server.server.output).group(1))
    fixture('server_renderer', SERVER_RENDERER_RE.search(server.server.output).group(1))
    frames = tracker.properties()['frame_count']
    assert frames >= min_frames, (
        f'expected to capture at least {min_frames} frames, but only got {frames}'
    )

@pytest.mark.performance
@pytest.mark.deps('pywayland-scanner', pip_pkgs=('pywayland',))
class TestScreencopyBandwidth:
    @pytest.mark.parametrize('app', [
        apps.qterminal('--execute', f'python3 -m asciinema play {ASCIINEMA_CAST}', pip_pkgs=('asciinema',), id='asciinema', extra=15),
        apps.snap('mir-kiosk-neverputt', extra=False)
    ])
    async def test_active_app(self, record_property, server, app) -> None:
        server = DisplayServer(server, add_extensions=ScreencopyTracker.required_extensions)
        tracker = ScreencopyTracker(server.display_name)
        async with server as s, tracker, s.program(app[0]) as p:
            if app[1]:
                await asyncio.wait_for(p.wait(), timeout=app[1])
            else:
                await asyncio.sleep(long_wait_time)
        _record_properties(record_property, server, tracker, 10)

    async def test_compositor_alone(self, record_property, server) -> None:
        server = DisplayServer(server, add_extensions=ScreencopyTracker.required_extensions)
        tracker = ScreencopyTracker(server.display_name)
        async with server, tracker:
            await asyncio.sleep(long_wait_time)
        _record_properties(record_property, server, tracker, 1)

    @pytest.mark.parametrize('app', [
        apps.qterminal(),
        apps.gedit(),
        apps.snap('mir-kiosk-kodi'),
    ])
    async def test_inactive_app(self, record_property, server, app) -> None:
        server = DisplayServer(server, add_extensions=ScreencopyTracker.required_extensions)
        tracker = ScreencopyTracker(server.display_name)
        async with server as s, tracker, s.program(app):
            await asyncio.sleep(long_wait_time)
        _record_properties(record_property, server, tracker, 2)

    @pytest.mark.parametrize('local_server', [
        apps.confined_shell(),
        apps.mir_test_tools(),
        apps.mir_demo_server(),
    ])
    async def test_app_dragged_around(self, record_property, local_server) -> None:
        async def pause():
            await asyncio.sleep(0.2)
        extensions = ScreencopyTracker.required_extensions + VirtualPointer.required_extensions
        app_path = Path(__file__).parent / 'clients' / 'maximizing_gtk_app.py'
        server = DisplayServer(local_server, add_extensions=extensions)
        app = server.program(('python3', str(app_path)))
        tracker = ScreencopyTracker(server.display_name)
        pointer = VirtualPointer(server.display_name)
        async with server, tracker, app, pointer:
            await asyncio.sleep(1)
            pointer.move_to_proportional(0.5, 0.03)
            await pause()
            pointer.button(Button.LEFT, True)
            await pause()
            for y in range(4):
                for x in range(4):
                    pointer.move_to_proportional((x + 0.5) / 4, (y + 0.5) / 4)
                    await pause()
        _record_properties(record_property, server, tracker, 16)
