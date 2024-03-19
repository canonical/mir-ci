import asyncio
import os
from pathlib import Path

import pytest
from mir_ci import SLOWDOWN
from mir_ci.fixtures import apps
from mir_ci.program.display_server import DisplayServer
from mir_ci.wayland.screencopy_tracker import ScreencopyTracker
from mir_ci.wayland.virtual_pointer import Button, VirtualPointer

long_wait_time = 10

ASCIINEMA_CAST = f"{os.path.dirname(__file__)}/data/demo.cast"


def _record_properties(fixture, server, tracker, min_frames):
    server.record_properties(fixture)
    for name, val in tracker.properties().items():
        fixture(name, val)
    frames = tracker.properties()["frame_count"]
    assert frames >= min_frames, f"expected to capture at least {min_frames} frames, but only got {frames}"


@pytest.mark.performance
class TestScreencopyBandwidth:
    @pytest.mark.parametrize(
        "app",
        [
            apps.qterminal(
                "--execute",
                f"python3 -m asciinema play {ASCIINEMA_CAST}",
                pip_pkgs=("asciinema",),
                id="asciinema",
                extra=20 + SLOWDOWN,
            ),
            apps.snap("mir-kiosk-neverputt", extra=False),
        ],
    )
    async def test_active_app(self, record_property, mir_server, app) -> None:
        mir_server = DisplayServer(mir_server, add_extensions=ScreencopyTracker.required_extensions)
        tracker = ScreencopyTracker(mir_server.display_name)
        async with mir_server as s, tracker, s.program(apps.App(app.command[0], app.app_type)) as p:
            if app.command[1]:
                await asyncio.wait_for(p.wait(timeout=app.command[1]), timeout=app.command[1] + 1)
            else:
                await asyncio.sleep(long_wait_time)
        _record_properties(record_property, mir_server, tracker, 10)

    async def test_compositor_alone(self, record_property, mir_server) -> None:
        mir_server = DisplayServer(mir_server, add_extensions=ScreencopyTracker.required_extensions)
        tracker = ScreencopyTracker(mir_server.display_name)
        async with mir_server, tracker:
            await asyncio.sleep(long_wait_time)
        _record_properties(record_property, mir_server, tracker, 1)

    @pytest.mark.parametrize(
        "app",
        [
            apps.qterminal(),
            apps.pluma(),
            apps.snap("mir-kiosk-kodi"),
        ],
    )
    async def test_inactive_app(self, record_property, mir_server, app) -> None:
        mir_server = DisplayServer(mir_server, add_extensions=ScreencopyTracker.required_extensions)
        tracker = ScreencopyTracker(mir_server.display_name)
        async with mir_server as s, tracker, s.program(app):
            await asyncio.sleep(long_wait_time)
        _record_properties(record_property, mir_server, tracker, 2)

    @pytest.mark.deps(debs=("libgtk-4-dev",), pip_pkgs=(("pygobject", "gi"),))
    @pytest.mark.parametrize(
        "local_server",
        [
            apps.confined_shell(),
            apps.mir_test_tools(),
            apps.mir_demo_server(),
        ],
    )
    async def test_app_dragged_around(self, record_property, local_server) -> None:
        async def pause():
            await asyncio.sleep(0.2)

        extensions = ScreencopyTracker.required_extensions + VirtualPointer.required_extensions
        app_path = Path(__file__).parent / "clients" / "maximizing_gtk_app.py"
        server = DisplayServer(local_server, add_extensions=extensions)
        app = server.program(apps.App(("python3", str(app_path))))
        tracker = ScreencopyTracker(server.display_name)
        pointer = VirtualPointer(server.display_name)
        async with server, tracker, app, pointer:
            await asyncio.sleep(2 * SLOWDOWN)  # TODO: detect when the window is drawn instead
            pointer.move_to_absolute(pointer.output_width / 2, 10)
            await pause()
            pointer.button(Button.LEFT, True)
            await pause()
            for y in range(4):
                for x in range(4):
                    pointer.move_to_proportional((x + 0.5) / 4, (y + 0.5) / 4)
                    await pause()
        _record_properties(record_property, server, tracker, 16)
