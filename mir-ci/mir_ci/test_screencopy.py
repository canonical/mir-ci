import tempfile
from pathlib import Path
from textwrap import dedent

import pytest
from mir_ci import SLOWDOWN, apps
from mir_ci.display_server import DisplayServer
from mir_ci.virtual_pointer import VirtualPointer
from mir_ci.screencopy_tracker import ScreencopyTracker

MIR_CI_PATH = Path(__file__).parent
APP_PATH = MIR_CI_PATH / "clients/drag_and_drop_demo.py"
STARTUP_TIME = 1.5 * SLOWDOWN
A_SHORT_TIME = 0.3

ROBOT_TEMPLATE = dedent("""\
*** Settings ***
{settings}

*** Test Cases ***
{test_case}
""")


@pytest.mark.parametrize(
    "server",
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
            # apps.snap("mir-kiosk-neverputt"),
            ("python3", APP_PATH, "--source", "pixbuf", "--target", "pixbuf", "--expect", "pixbuf"),
        ],
    )
    @pytest.mark.deps(debs=("libgtk-4-dev",), pip_pkgs=(("pygobject", "gi"),))
    async def test_screencopy_match(self, server, app) -> None:
        extensions = VirtualPointer.required_extensions + ScreencopyTracker.required_extensions
        server = DisplayServer(server, add_extensions=extensions)
        # program = server.program(app)
        program = server.program(apps.App(app))

        robot_settings = dedent(f"""\
            Library    {MIR_CI_PATH}/robot/libraries/WaylandHid.py
            Library    {MIR_CI_PATH}/robot/libraries/Screencopy.py
        """).strip("\n")

        robot_test_case = dedent(f"""\
            Screencopy Match
                Sleep    {STARTUP_TIME}
                # Record As Gif    temp.gif    1
                Record As Video    temp.avi    5
                Move Pointer To Absolute    40    40
                Sleep    {A_SHORT_TIME}
                Press LEFT Button
                Sleep    {A_SHORT_TIME}
                Move Pointer To Absolute    120    70
                Sleep    {A_SHORT_TIME}
                Move Pointer To Absolute    200    100
                Sleep    {A_SHORT_TIME}
                Release LEFT Button
        """).strip("\n")

        # robot_test_case = f"""Screencopy Match
        #     Sleep     {STARTUP_TIME}
        #     ${{regions}} =    Wait Match    {MIR_CI_PATH / "robot/templates/drag_and_drop_src.png"}
        #     ${{length}} =    Get Length    ${{regions}}
        #     LOG    Number of regions: ${{length}}
        #     FOR    ${{region}}    IN    @{{regions}}
        #         ${{center}} =    Get Center    ${{region}}
        #         Log    ${{center}}
        #     END
        # """

        with tempfile.NamedTemporaryFile(mode="w+", suffix=".robot", buffering=1) as robot_file:
            robot_file.write(ROBOT_TEMPLATE.format(settings=robot_settings, test_case=robot_test_case))
            robot = server.program(apps.App(("robot", robot_file.name)))
            # robot = server.program(apps.App(("robot", "-o", "NONE", "-r", "NONE", robot_file.name)))

            async with server, program, robot:
                await robot.wait()
                await program.kill()
