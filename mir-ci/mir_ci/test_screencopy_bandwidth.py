import asyncio
import os
from pathlib import Path
from textwrap import dedent

import pytest
from mir_ci import SLOWDOWN, apps
from mir_ci.display_server import DisplayServer
from mir_ci.robot_wrapper import WaylandRobot
from mir_ci.screencopy_tracker import ScreencopyTracker

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
    async def test_active_app(self, record_property, server, app) -> None:
        server = DisplayServer(server, add_extensions=ScreencopyTracker.required_extensions)
        tracker = ScreencopyTracker(server.display_name)
        async with server as s, tracker, s.program(apps.App(app.command[0], app.app_type)) as p:
            if app.command[1]:
                await asyncio.wait_for(p.wait(timeout=app.command[1]), timeout=app.command[1] + 1)
            else:
                await asyncio.sleep(long_wait_time)
        _record_properties(record_property, server, tracker, 10)

    async def test_compositor_alone(self, record_property, server) -> None:
        server = DisplayServer(server, add_extensions=ScreencopyTracker.required_extensions)
        tracker = ScreencopyTracker(server.display_name)
        async with server, tracker:
            await asyncio.sleep(long_wait_time)
        _record_properties(record_property, server, tracker, 1)

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

    @pytest.mark.deps(
        debs=("libgtk-4-dev",),
        pip_pkgs=(
            ("pygobject", "gi"),
            ("robotframework~=6.1.1", "robot"),
            ("rpaframework", "RPA"),
            ("rpaframework-recognition", "RPA.recognition"),
        ),
    )
    @pytest.mark.parametrize(
        "local_server",
        [
            apps.confined_shell(),
            apps.mir_test_tools(),
            apps.mir_demo_server(),
        ],
    )
    @pytest.mark.parametrize(
        "client",
        [apps.gtkapp("python3", Path(__file__).parent / "clients" / "maximizing_gtk_app.py")],
    )
    async def test_app_dragged_around(self, record_property, local_server, client, request) -> None:
        extensions = ScreencopyTracker.required_extensions + WaylandRobot.required_extensions
        server = DisplayServer(local_server, add_extensions=extensions)
        tracker = ScreencopyTracker(server.display_name)

        robot_test_case = dedent(
            """\
            Drag app
                ${pos}=    Move Pointer To Template    ${template_path}/dragged_app_titlebar.png
                Press LEFT Button
                FOR     ${y}    IN RANGE    4
                    FOR     ${x}    IN RANGE    4
                        ${px}   evaluate    ($x + 0.5) / 4
                        ${py}   evaluate    ($y + 0.5) / 4
                        Move Pointer To Proportional    ${px}   ${py}
                        Sleep   0.2
                    END
                END
        """
        )

        robot = server.program(WaylandRobot(request, robot_test_case))

        async with server, tracker, server.program(client), robot:
            await robot.wait()
        _record_properties(record_property, server, tracker, 16)
