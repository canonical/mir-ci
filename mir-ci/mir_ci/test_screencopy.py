import tempfile
from pathlib import Path
from textwrap import dedent

import pytest
from mir_ci import SLOWDOWN, apps
from mir_ci.display_server import DisplayServer
from mir_ci.virtual_pointer import VirtualPointer
from mir_ci.screencopy_tracker import ScreencopyTracker
# from mir_ci.robot.libraries.Screencopy import Screencopy

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
        apps.confined_shell(),
        apps.mir_test_tools(),
        apps.mir_demo_server(),
    ],
)
class TestDragAndDrop:
    @pytest.mark.parametrize(
        "app",
        [
            # apps.snap("mir-kiosk-neverputt"),
            ("python3", APP_PATH, "--source", "pixbuf", "--target", "pixbuf", "--expect", "pixbuf"),
            ("python3", APP_PATH, "--source", "text", "--target", "text", "--expect", "text"),
        ],
    )
    @pytest.mark.deps(debs=("libgtk-4-dev",), pip_pkgs=(("pygobject", "gi"),))
    async def test_screencopy_match(self, server, app, request) -> None:
        extensions = VirtualPointer.required_extensions + ScreencopyTracker.required_extensions
        server_instance = DisplayServer(server, add_extensions=extensions)
        # program = server_instance.program(app)
        program = server_instance.program(apps.App(app))
        test_case_name = request.node.name

        robot_settings = dedent(f"""\
            Library     {MIR_CI_PATH}/robot/libraries/WaylandHid.py
            Library     {MIR_CI_PATH}/robot/libraries/Screencopy.py
        """).strip("\n")

        #         # Record As Gif    temp.gif    1
        #         # Record As Video    temp.avi    5

        # robot_test_case = dedent(f"""\
        #     Screencopy Match
        #         Sleep    {STARTUP_TIME}
        #         Take Screenshot    {test_case_name}    {MIR_CI_PATH}/robot/log/{test_case_name}
        #         Move Pointer To Absolute    40    40
        #         Sleep    {A_SHORT_TIME}
        #         Take Screenshot    {test_case_name}    {MIR_CI_PATH}/robot/log/{test_case_name}
        #         Press LEFT Button
        #         Sleep    {A_SHORT_TIME}
        #         Take Screenshot    {test_case_name}    {MIR_CI_PATH}/robot/log/{test_case_name}
        #         Move Pointer To Absolute    120    70
        #         Sleep    {A_SHORT_TIME}
        #         Take Screenshot    {test_case_name}    {MIR_CI_PATH}/robot/log/{test_case_name}
        #         Move Pointer To Absolute    200    100
        #         Sleep    {A_SHORT_TIME}
        #         Take Screenshot    {test_case_name}    {MIR_CI_PATH}/robot/log/{test_case_name}
        #         Release LEFT Button
        #         Sleep    {A_SHORT_TIME}
        #         Take Screenshot    {test_case_name}    {MIR_CI_PATH}/robot/log/{test_case_name}
        #         Sleep    {A_SHORT_TIME}
        #         Take Screenshot    {test_case_name}    {MIR_CI_PATH}/robot/log/{test_case_name}
        #         Create Video From Screenshots    {MIR_CI_PATH}/robot/log/{test_case_name}    ${{None}}    True
        # """).strip("\n")

        robot_test_case = dedent(f"""\
            Screencopy Match
                Sleep     {STARTUP_TIME}
                ${{regions}} =    Test Match    {MIR_CI_PATH}/robot/templates/drag_and_drop_src.png
                Move Pointer To Absolute    ${{regions}}[0][center_x]    ${{regions}}[0][center_y]
                Sleep    {A_SHORT_TIME}
                Press LEFT Button
                Sleep    {A_SHORT_TIME}
                ${{regions}} =    Wait Match    {MIR_CI_PATH}/robot/templates/drag_and_drop_dst.png
                Move Pointer To Absolute    ${{regions}}[0][center_x]    ${{regions}}[0][center_y]
                Sleep    {A_SHORT_TIME}
                Release LEFT Button
        """).strip("\n")

        # robot_test_case = dedent(f"""\
        #     Screencopy Match
        #         Sleep     {STARTUP_TIME}
        #         ${{regions}} =    Wait Match    {MIR_CI_PATH}/robot/templates/drag_and_drop_src.png
        #         ${{length}} =    Get Length    ${{regions}}
        #         LOG    Number of regions: ${{length}}
        #         FOR    ${{region}}    IN    @{{regions}}
        #             Log    ${{region}}
        #             ${{center}} =    Get Center    ${{region}}
        #             Log    ${{center}}
        #         END
        # """).strip("\n")

        with tempfile.NamedTemporaryFile(mode="w+", suffix=".robot", buffering=1) as robot_file:
            robot_file.write(ROBOT_TEMPLATE.format(settings=robot_settings, test_case=robot_test_case))

            listener_path = f"{MIR_CI_PATH}/robot/libraries/ScreencopyListener.py"
            screenshots_path = f"{MIR_CI_PATH}/robot/log/{test_case_name}"
            delete_screenshots = True
            robot_listener = f"{listener_path}:{test_case_name}:{screenshots_path}:{delete_screenshots}"
            robot = server_instance.program(apps.App(("robot", "--listener", robot_listener, robot_file.name)))
            # robot = server_instance.program(apps.App(("robot", "-o", "NONE", "-r", "NONE", robot_file.name)))

            async with server_instance, program, robot:
                await robot.wait()
                await program.kill()

        # screencopy = Screencopy()
        # screencopy.create_video_from_screenshots(Path("temp.avi"))
        # screencopy.delete_screenshots()
