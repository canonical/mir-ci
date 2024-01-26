import tempfile
from pathlib import Path

import pytest
from mir_ci import SLOWDOWN, apps
from mir_ci.display_server import DisplayServer
from mir_ci.virtual_pointer import VirtualPointer
from mir_ci.screencopy_tracker import ScreencopyTracker

MIR_CI_PATH = Path(__file__).parent
APP_PATH = MIR_CI_PATH / "clients/drag_and_drop_demo.py"
ROBOT_LIBRARY_PATH = MIR_CI_PATH / "robot/libraries/WaylandHid.py"
ROBOT_LIBRARY_PATH2 = MIR_CI_PATH / "robot/libraries/Screencopy.py"
STARTUP_TIME = 1.5 * SLOWDOWN
A_SHORT_TIME = 0.3

ROBOT_TEMPLATE = """*** Settings ***
Library    {library_path}
Library    {library_path2}

*** Test Cases ***
{test_case}
"""


@pytest.mark.parametrize(
    "modern_server",
    [
        apps.ubuntu_frame(),
        # apps.mir_kiosk(), we need servers based on Mir 2.14 or later
        # apps.confined_shell(),
        # apps.mir_test_tools(),
        # apps.mir_demo_server(),
    ],
)
class TestDragAndDrop:
    @pytest.mark.parametrize(
        "app",
        [
            ("python3", APP_PATH, "--source", "pixbuf", "--target", "pixbuf", "--expect", "pixbuf"),
        ],
    )
    @pytest.mark.deps(debs=("libgtk-4-dev",), pip_pkgs=(("pygobject", "gi"),))
    async def test_screencopy_match(self, modern_server, app) -> None:
        extensions = VirtualPointer.required_extensions + ScreencopyTracker.required_extensions
        modern_server = DisplayServer(modern_server, add_extensions=extensions)
        program = modern_server.program(apps.App(app))

        robot_test_case = f"""Screencopy Match
            Sleep     {STARTUP_TIME}
            Move Pointer To Absolute    40    40
            Sleep     {A_SHORT_TIME}
            Press LEFT Button
            Save Frame
            Sleep     {A_SHORT_TIME}
            Move Pointer To Absolute    120    70
            Sleep     {A_SHORT_TIME}
            Move Pointer To Absolute    200    100
            Sleep     {A_SHORT_TIME}
            Release LEFT Button
        """

        with tempfile.NamedTemporaryFile(mode="w+", suffix=".robot", buffering=1) as robot_file:
            robot_file.write(ROBOT_TEMPLATE.format(library_path=ROBOT_LIBRARY_PATH, library_path2=ROBOT_LIBRARY_PATH2, test_case=robot_test_case))
            robot = modern_server.program(apps.App(("robot", "-o", "NONE", "-r", "NONE", robot_file.name)))

            async with modern_server, program, robot:
                await robot.wait()
                await program.wait()
