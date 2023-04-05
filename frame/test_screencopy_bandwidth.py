from display_server import DisplayServer
from screencopy_tracker import ScreencopyTracker
import pytest
import os
import asyncio

import apps

long_wait_time = 10

ASCIINEMA_CAST = f'{os.path.dirname(__file__)}/data/demo.cast'

def record_screencopy_properties(record_property, tracker: ScreencopyTracker, min_frames: int):
    for name, val in tracker.properties().items():
        record_property(name, val)
    frames = tracker.properties()['frame count']
    assert frames >= min_frames, (
        f'expected to capture at least {min_frames} frames, but only got {frames}'
    )

@pytest.mark.performance
class TestScreencopyBandwidth:
    @pytest.mark.parametrize('app', [
        apps.qterminal('--execute', f'python3 -m asciinema play {ASCIINEMA_CAST}', pip_pkgs=('asciinema',), id='asciinema', extra=15),
        apps.snap('mir-kiosk-neverputt', extra=False)
    ])
    async def test_active_app(self, record_property, server, app) -> None:
        with DisplayServer(server, add_extensions=ScreencopyTracker.required_extensions) as s:
            tracker = ScreencopyTracker(s.display_name)
            with tracker, s.program(app[0]) as p:
                if app[1]:
                    p.wait(app[1])
                else:
                    await asyncio.sleep(long_wait_time)
            record_screencopy_properties(record_property, tracker, 10)

    async def test_compositor_alone(self, record_property, server) -> None:
        with DisplayServer(server, add_extensions=ScreencopyTracker.required_extensions) as s:
            tracker = ScreencopyTracker(s.display_name)
            with tracker:
                await asyncio.sleep(long_wait_time)
            record_screencopy_properties(record_property, tracker, 1)

    @pytest.mark.parametrize('app', [
        apps.qterminal(),
        apps.gedit(),
        apps.snap('mir-kiosk-kodi'),
    ])
    async def test_inactive_app(self, record_property, server, app) -> None:
        with DisplayServer(server, add_extensions=ScreencopyTracker.required_extensions) as s:
            tracker = ScreencopyTracker(s.display_name)
            with tracker, s.program(app):
                await asyncio.sleep(long_wait_time)
            record_screencopy_properties(record_property, tracker, 2)
