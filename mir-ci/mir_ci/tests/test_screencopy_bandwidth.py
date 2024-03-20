import asyncio
import os
from pathlib import Path

import pytest
from mir_ci import SLOWDOWN
from mir_ci.fixtures import apps, servers
from mir_ci.program.app import App
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
    @pytest.mark.parametrize("server", servers.servers(servers.ServerCap.SCREENCOPY))
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
    async def test_active_app(self, record_property, server, app) -> None:
        server = DisplayServer(server, add_extensions=ScreencopyTracker.required_extensions)
        tracker = ScreencopyTracker(server.display_name)
        async with server as s, tracker, s.program(App(app.command[0], app.app_type)) as p:
            if app.command[1]:
                await asyncio.wait_for(p.wait(timeout=app.command[1]), timeout=app.command[1] + 1)
            else:
                await asyncio.sleep(long_wait_time)
        _record_properties(record_property, server, tracker, 10)

    @pytest.mark.parametrize("server", servers.servers(servers.ServerCap.SCREENCOPY))
    async def test_compositor_alone(self, record_property, server) -> None:
        server = DisplayServer(server, add_extensions=ScreencopyTracker.required_extensions)
        tracker = ScreencopyTracker(server.display_name)
        async with server, tracker:
            await asyncio.sleep(long_wait_time)
        _record_properties(record_property, server, tracker, 1)

    @pytest.mark.parametrize("server", servers.servers(servers.ServerCap.SCREENCOPY))
    @pytest.mark.parametrize(
        "app",
        [
            apps.qterminal(),
            apps.pluma(),
            apps.snap("mir-kiosk-kodi"),
        ],
    )
    async def test_inactive_app(self, record_property, server, app) -> None:
        server = DisplayServer(server, add_extensions=ScreencopyTracker.required_extensions)
        tracker = ScreencopyTracker(server.display_name)
        async with server as s, tracker, s.program(app):
            await asyncio.sleep(long_wait_time)
        _record_properties(record_property, server, tracker, 2)

    @pytest.mark.deps(debs=("libgtk-4-dev",), pip_pkgs=(("pygobject", "gi"),))
    @pytest.mark.parametrize(
        "local_server",
        [
            servers.confined_shell(),
            servers.mir_test_tools(),
            servers.mir_demo_server(),
        ],
    )
    async def test_app_dragged_around(self, record_property, local_server) -> None:
        async def pause():
            await asyncio.sleep(0.2)

        extensions = ScreencopyTracker.required_extensions + VirtualPointer.required_extensions
        app_path = Path(__file__).parent / "clients" / "maximizing_gtk_app.py"
        server = DisplayServer(local_server, add_extensions=extensions)
        app = server.program(App(("python3", str(app_path))))
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
