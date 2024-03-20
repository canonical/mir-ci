import tempfile
from pathlib import Path
from textwrap import dedent

import pytest
from mir_ci.fixtures import servers
from mir_ci.program.app import App
from mir_ci.program.display_server import DisplayServer
from mir_ci.wayland.screencopy_tracker import ScreencopyTracker
from mir_ci.wayland.virtual_pointer import VirtualPointer

TESTS_PATH = Path(__file__).parent
APP_PATH = TESTS_PATH / "clients" / "drag_and_drop_demo.py"

ROBOT_TEMPLATE = """\
*** Settings ***
{settings}

*** Variables ***
{variables}

*** Test Cases ***
{test_case}
"""
ROBOT_SETTINGS = f"Resource   {TESTS_PATH}/robot/resources/KVM.resource"
ROBOT_VARIABLES = f"""\
${{SRC_TEMPLATE}}    {TESTS_PATH}/robot/templates/drag_and_drop_src.png
${{DST_TEMPLATE}}    {TESTS_PATH}/robot/templates/drag_and_drop_dst.png
${{END_TEMPLATE}}    {TESTS_PATH}/robot/templates/drag_and_drop_end.png
"""


@pytest.mark.xdg(
    XDG_CONFIG_HOME={
        "glib-2.0/settings/keyfile": dedent(
            """\
            [org/gnome/desktop/interface]
            color-scheme='prefer-light'
            gtk-theme='Adwaita'
            icon-theme='Adwaita'
            font-name='Ubuntu 11'
            cursor-theme='Adwaita'
            cursor-size=24
            font-antialiasing='grayscale'
        """
        ),
    },
)
@pytest.mark.env(GSETTINGS_BACKEND="keyfile")
@pytest.mark.parametrize(
    "modern_server",
    [
        servers.ubuntu_frame(),
        # servers.mir_kiosk(), we need servers based on Mir 2.14 or later
        servers.confined_shell(),
        servers.mir_test_tools(),
        servers.mir_demo_server(),
    ],
)
@pytest.mark.deps(
    debs=(
        "libgirepository1.0-dev",
        "libgtk-3-dev",
        "fonts-ubuntu",
        "adwaita-icon-theme-full",
    ),
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
    async def test_source_and_dest_match(self, modern_server, app, tmp_path) -> None:
        extensions = VirtualPointer.required_extensions + ScreencopyTracker.required_extensions
        server_instance = DisplayServer(modern_server, add_extensions=extensions)
        program = server_instance.program(App(app))

        robot_test_case = dedent(
            """\
            Source and Destination Match
                Move Pointer To ${SRC_TEMPLATE}
                Press LEFT Button
                Walk Pointer To ${DST_TEMPLATE}
                Release LEFT Button
        """
        )

        with tempfile.NamedTemporaryFile(mode="w+", suffix=".robot", buffering=1) as robot_file:
            robot_file.write(
                ROBOT_TEMPLATE.format(settings=ROBOT_SETTINGS, variables=ROBOT_VARIABLES, test_case=robot_test_case)
            )
            robot = server_instance.program(App(("robot", "-d", tmp_path, robot_file.name)))

            async with server_instance, program, robot:
                await robot.wait(60)
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
    async def test_source_and_dest_mismatch(self, modern_server, app, tmp_path) -> None:
        extensions = VirtualPointer.required_extensions + ScreencopyTracker.required_extensions
        server_instance = DisplayServer(modern_server, add_extensions=extensions)
        program = server_instance.program(App(app))

        robot_test_case = dedent(
            """\
            Source and Destination Mismatch
                Move Pointer To ${SRC_TEMPLATE}
                Press LEFT Button
                Walk Pointer To ${DST_TEMPLATE}
                Release LEFT Button
                Walk Pointer To ${END_TEMPLATE}
        """
        )

        with tempfile.NamedTemporaryFile(mode="w+", suffix=".robot", buffering=1) as robot_file:
            robot_file.write(
                ROBOT_TEMPLATE.format(settings=ROBOT_SETTINGS, variables=ROBOT_VARIABLES, test_case=robot_test_case)
            )
            robot = server_instance.program(App(("robot", "-d", tmp_path, robot_file.name)))

            async with server_instance, program, robot:
                await robot.wait(60)
                assert program.is_running()
                await program.kill()
            assert "drag-begin\ndrag-failed\nenter-notify-event: dropbox" in program.output
