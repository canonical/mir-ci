import tempfile
from pathlib import Path

import pytest
from mir_ci import SLOWDOWN, apps
from mir_ci.display_server import DisplayServer
from mir_ci.virtual_pointer import VirtualPointer

MIR_CI_PATH = str(Path(__file__).parent)
APP_PATH = MIR_CI_PATH + "/clients/drag_and_drop_demo.py"
STARTUP_TIME = 1.5 * SLOWDOWN
A_SHORT_TIME = 0.3
ROBOT_HEADER = f"""*** Settings ***
Library    {MIR_CI_PATH}/robot/libraries/WaylandHid.py
"""


@pytest.mark.parametrize(
    "modern_server",
    [
        apps.ubuntu_frame(),
        # apps.mir_kiosk(), we need servers based on Mir 2.14 or later
        apps.confined_shell(),
        apps.mir_test_tools(),
        apps.mir_demo_server(),
    ],
)
class TestDragAndDrop:
    @pytest.mark.parametrize(
        "app",
        [
            ("python3", APP_PATH, "--source", "pixbuf", "--target", "pixbuf", "--expect", "pixbuf"),
            ("python3", APP_PATH, "--source", "text", "--target", "text", "--expect", "text"),
        ],
    )
    @pytest.mark.deps(debs=("libgtk-4-dev",), pip_pkgs=(("pygobject", "gi"),))
    async def test_source_and_dest_match(self, modern_server, app) -> None:
        modern_server = DisplayServer(modern_server, add_extensions=VirtualPointer.required_extensions)
        program = modern_server.program(apps.App(app))

        robot_test_case = f"""Source and Destination Match
            Sleep     {STARTUP_TIME}
            Move Pointer To Absolute    40    40
            Sleep     {A_SHORT_TIME}
            Press LEFT Button
            Sleep     {A_SHORT_TIME}
            Move Pointer To Absolute    120    70
            Sleep     {A_SHORT_TIME}
            Move Pointer To Absolute    200    100
            Sleep     {A_SHORT_TIME}
            Release LEFT Button
        """

        with tempfile.NamedTemporaryFile(mode="w+", suffix=".robot", buffering=1) as robot_file:
            robot_file.write(ROBOT_HEADER + "\n*** Test Cases ***\n" + robot_test_case)
            robot = modern_server.program(apps.App(("robot", "-o", "NONE", "-r", "NONE", robot_file.name)))

            async with modern_server, program, robot:
                await robot.wait()
                await program.wait()

    @pytest.mark.parametrize(
        "app",
        [
            ("python3", "-u", APP_PATH, "--source", "pixbuf", "--target", "text", "--expect", "pixbuf"),
            ("python3", "-u", APP_PATH, "--source", "text", "--target", "pixbuf", "--expect", "text"),
            ("python3", "-u", APP_PATH, "--source", "pixbuf", "--target", "text", "--expect", "text"),
            ("python3", "-u", APP_PATH, "--source", "text", "--target", "pixbuf", "--expect", "pixbuf"),
        ],
    )
    @pytest.mark.deps(debs=("libgtk-4-dev",), pip_pkgs=(("pygobject", "gi"),))
    async def test_source_and_dest_mismatch(self, modern_server, app) -> None:
        modern_server = DisplayServer(modern_server, add_extensions=VirtualPointer.required_extensions)
        program = modern_server.program(apps.App(app))

        robot_test_case = f"""Source and Destination Mismatch
            Sleep     {STARTUP_TIME}
            Move Pointer To Absolute    40    40
            Sleep     {A_SHORT_TIME}
            Press LEFT Button
            Sleep     {A_SHORT_TIME}
            Move Pointer To Absolute    120    70
            Sleep     {A_SHORT_TIME}
            Move Pointer To Absolute    200    100
            Sleep     {A_SHORT_TIME}
            Release LEFT Button
            Sleep     {A_SHORT_TIME}
            Move Pointer To Absolute    220    120
            Sleep     {A_SHORT_TIME}
        """

        with tempfile.NamedTemporaryFile(mode="w+", suffix=".robot", buffering=1) as robot_file:
            robot_file.write(ROBOT_HEADER + "\n*** Test Cases ***\n" + robot_test_case)
            robot = modern_server.program(apps.App(("robot", "-o", "NONE", "-r", "NONE", robot_file.name)))

            async with modern_server, program, robot:
                await robot.wait()
                assert program.is_running()
                await program.kill()
            assert "drag-begin\ndrag-failed\nenter-notify-event: dropbox" in program.output
