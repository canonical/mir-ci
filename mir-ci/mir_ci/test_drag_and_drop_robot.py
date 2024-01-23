from pathlib import Path

import pytest
from mir_ci import apps
from mir_ci.display_server import DisplayServer
from mir_ci.virtual_pointer import VirtualPointer

APP_PATH = Path(__file__).parent / "clients" / "drag_and_drop_demo.py"
ROBOT_PATH = Path(__file__).parent / "robot" / "tests" / "drag_and_drop.robot"


@pytest.mark.parametrize(
    "modern_server",
    [
        apps.ubuntu_frame(),
        # apps.mir_kiosk(), we need servers based on Mir 2.14 or later
        # apps.confined_shell(),
        apps.mir_test_tools(),
        apps.mir_demo_server(),
    ],
)
class TestDragAndDrop:
    @pytest.mark.parametrize(
        "app",
        [
            ("python3", str(APP_PATH), "--source", "pixbuf", "--target", "pixbuf", "--expect", "pixbuf"),
            ("python3", str(APP_PATH), "--source", "text", "--target", "text", "--expect", "text"),
        ],
    )
    @pytest.mark.deps(debs=("libgtk-4-dev",), pip_pkgs=(("pygobject", "gi"),))
    async def test_source_and_dest_match(self, modern_server, app) -> None:
        modern_server = DisplayServer(modern_server, add_extensions=VirtualPointer.required_extensions)
        program = modern_server.program(apps.App(app))
        robot = modern_server.program(apps.App(("robot", "-d", "robot/result", "-i", "match", str(ROBOT_PATH))))

        async with modern_server, program, robot:
            await program.wait()

    @pytest.mark.parametrize(
        "app",
        [
            ("python3", "-u", str(APP_PATH), "--source", "pixbuf", "--target", "text", "--expect", "pixbuf"),
            ("python3", "-u", str(APP_PATH), "--source", "text", "--target", "pixbuf", "--expect", "text"),
            ("python3", "-u", str(APP_PATH), "--source", "pixbuf", "--target", "text", "--expect", "text"),
            ("python3", "-u", str(APP_PATH), "--source", "text", "--target", "pixbuf", "--expect", "pixbuf"),
        ],
    )
    @pytest.mark.deps(debs=("libgtk-4-dev",), pip_pkgs=(("pygobject", "gi"),))
    async def test_source_and_dest_mismatch(self, modern_server, app) -> None:
        modern_server = DisplayServer(modern_server, add_extensions=VirtualPointer.required_extensions)
        program = modern_server.program(apps.App(app))
        robot = modern_server.program(apps.App(("robot", "-d", "robot/result", "-i", "mismatch", str(ROBOT_PATH))))

        async with modern_server, program, robot:
            assert program.is_running()
            await robot.wait()
            await program.kill()
        assert "drag-begin\ndrag-failed\nenter-notify-event: dropbox" in program.output
