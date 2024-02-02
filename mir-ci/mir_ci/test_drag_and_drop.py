import tempfile
from pathlib import Path
from textwrap import dedent

import pytest
from mir_ci import SLOWDOWN, apps
from mir_ci.display_server import DisplayServer
from mir_ci.screencopy_tracker import ScreencopyTracker
from mir_ci.virtual_pointer import VirtualPointer

MIR_CI_PATH = Path(__file__).parent
APP_PATH = MIR_CI_PATH / "clients/drag_and_drop_demo.py"
STARTUP_TIME = 1.5 * SLOWDOWN
A_SHORT_TIME = 0.3

ROBOT_TEMPLATE = dedent(
    """\
*** Settings ***
{settings}

*** Test Cases ***
{test_case}
"""
)


@pytest.mark.xdg(XDG_CONFIG_HOME={"gtk-3.0/settings.ini": "[Settings]\ngtk-application-prefer-dark-theme = true\n"})
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
@pytest.mark.deps(
    debs=("libgtk-4-dev",),
    pip_pkgs=(
        ("pygobject", "gi"),
        ("robotframework~=6.1.1", "robot"),
        ("rpaframework", "RPA"),
        ("rpaframework-recognition", "RPA.recognition"),
    ),
)
class TestDragAndDrop:
    @pytest.mark.parametrize(
        "app",
        [
            ("python3", APP_PATH, "--source", "pixbuf", "--target", "pixbuf", "--expect", "pixbuf"),
            ("python3", APP_PATH, "--source", "text", "--target", "text", "--expect", "text"),
        ],
    )
    async def test_source_and_dest_match(self, server, app) -> None:
        extensions = VirtualPointer.required_extensions + ScreencopyTracker.required_extensions
        server_instance = DisplayServer(server, add_extensions=extensions)
        program = server_instance.program(apps.App(app))

        robot_settings = dedent(
            f"""\
            Library    {MIR_CI_PATH}/robot_libraries/WaylandHid.py
            Library    {MIR_CI_PATH}/robot_libraries/Screencopy.py
            Resource   {MIR_CI_PATH}/robot_resources/screencopy.resource
        """
        ).strip("\n")

        robot_test_case = dedent(
            f"""\
            Source and Destination Match
                Sleep     {STARTUP_TIME}
                ${{regions}} =    Test Match    {MIR_CI_PATH}/robot_templates/drag_and_drop_src.png
                ${{center}} =    Get Center    ${{regions}}[0]
                Move Pointer To Absolute    ${{center}}[x]    ${{center}}[y]
                Sleep     {A_SHORT_TIME}
                Press LEFT Button
                ${{off_center}} =    Add Displacement    ${{center}}    20    20
                Move Pointer To Absolute    ${{off_center}}[x]    ${{off_center}}[y]
                Sleep     {A_SHORT_TIME}
                ${{regions}} =    Test Match    {MIR_CI_PATH}/robot_templates/drag_and_drop_dst.png
                ${{center}} =    Get Center    ${{regions}}[0]
                Move Pointer To Absolute    ${{center}}[x]    ${{center}}[y]
                Sleep     {A_SHORT_TIME}
                Release LEFT Button
        """
        ).strip("\n")

        with tempfile.NamedTemporaryFile(mode="w+", suffix=".robot", buffering=1) as robot_file:
            robot_file.write(ROBOT_TEMPLATE.format(settings=robot_settings, test_case=robot_test_case))
            robot = server_instance.program(apps.App(("robot", "-o", "NONE", "-r", "NONE", robot_file.name)))

            async with server_instance, program, robot:
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
    async def test_source_and_dest_mismatch(self, server, app) -> None:
        extensions = VirtualPointer.required_extensions + ScreencopyTracker.required_extensions
        server_instance = DisplayServer(server, add_extensions=extensions)
        program = server_instance.program(apps.App(app))

        robot_settings = dedent(
            f"""\
            Library    {MIR_CI_PATH}/robot_libraries/WaylandHid.py
            Library    {MIR_CI_PATH}/robot_libraries/Screencopy.py
            Resource   {MIR_CI_PATH}/robot_resources/screencopy.resource
        """
        ).strip("\n")

        robot_test_case = dedent(
            f"""\
            Source and Destination Mismatch
                Sleep    {STARTUP_TIME}
                ${{regions}} =    Test Match    {MIR_CI_PATH}/robot_templates/drag_and_drop_src.png
                ${{center}} =    Get Center    ${{regions}}[0]
                Move Pointer To Absolute    ${{center}}[x]    ${{center}}[y]
                Sleep    {A_SHORT_TIME}
                Press LEFT Button
                Sleep    {A_SHORT_TIME}
                ${{off_center}} =    Add Displacement    ${{center}}    20    20
                Move Pointer To Absolute    ${{off_center}}[x]    ${{off_center}}[y]
                Sleep    {A_SHORT_TIME}
                ${{regions}} =    Test Match    {MIR_CI_PATH}/robot_templates/drag_and_drop_dst.png
                ${{center}} =    Get Center    ${{regions}}[0]
                Move Pointer To Absolute    ${{center}}[x]    ${{center}}[y]
                Sleep    {A_SHORT_TIME}
                Release LEFT Button
                Sleep    {A_SHORT_TIME}
                ${{off_center}} =    Add Displacement    ${{center}}    20    20
                Move Pointer To Absolute    ${{off_center}}[x]    ${{off_center}}[y]
                Sleep    {A_SHORT_TIME}
        """
        ).strip("\n")

        with tempfile.NamedTemporaryFile(mode="w+", suffix=".robot", buffering=1) as robot_file:
            robot_file.write(ROBOT_TEMPLATE.format(settings=robot_settings, test_case=robot_test_case))
            robot = server_instance.program(apps.App(("robot", "-o", "NONE", "-r", "NONE", robot_file.name)))

            async with server_instance, program, robot:
                await robot.wait()
                assert program.is_running()
                await program.kill()
            assert "drag-begin\ndrag-failed\nenter-notify-event: dropbox" in program.output
