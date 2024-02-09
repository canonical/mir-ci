from pathlib import Path
from textwrap import dedent

import pytest
from mir_ci import apps
from mir_ci.display_server import DisplayServer
from mir_ci.robot_wrapper import WaylandRobot
from mir_ci.screencopy_tracker import ScreencopyTracker
from mir_ci.virtual_pointer import VirtualPointer

APP_PATH = Path(__file__).parent / "clients/drag_and_drop_demo.py"


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
            apps.gtkapp("python3", APP_PATH, "--source", "pixbuf", "--target", "pixbuf", "--expect", "pixbuf"),
            apps.gtkapp("python3", APP_PATH, "--source", "text", "--target", "text", "--expect", "text"),
        ],
    )
    async def test_source_and_dest_match(self, modern_server, app, request) -> None:
        extensions = VirtualPointer.required_extensions + ScreencopyTracker.required_extensions
        server_instance = DisplayServer(modern_server, add_extensions=extensions)
        program = server_instance.program(app)

        robot_test_case = dedent(
            """\
            Source and Destination Match
                ${pos}=    Move Pointer To ${template_path}/drag_and_drop_src.png
                Press LEFT Button
                Walk Pointer From ${pos} To ${template_path}/drag_and_drop_dst.png
                Release LEFT Button
        """
        )

        robot = server_instance.program(WaylandRobot(request, robot_test_case))

        async with server_instance, program, robot:
            await robot.wait(60)
            await program.wait()

    @pytest.mark.parametrize(
        "app",
        [
            apps.gtkapp("python3", "-u", APP_PATH, "--source", "pixbuf", "--target", "text", "--expect", "pixbuf"),
            apps.gtkapp("python3", "-u", APP_PATH, "--source", "text", "--target", "pixbuf", "--expect", "text"),
            apps.gtkapp("python3", "-u", APP_PATH, "--source", "pixbuf", "--target", "text", "--expect", "text"),
            apps.gtkapp("python3", "-u", APP_PATH, "--source", "text", "--target", "pixbuf", "--expect", "pixbuf"),
        ],
    )
    async def test_source_and_dest_mismatch(self, modern_server, app, request) -> None:
        extensions = VirtualPointer.required_extensions + ScreencopyTracker.required_extensions
        server_instance = DisplayServer(modern_server, add_extensions=extensions)
        program = server_instance.program(app)

        robot_test_case = dedent(
            """\
            Source and Destination Mismatch
                ${pos}=    Move Pointer To ${template_path}/drag_and_drop_src.png
                Press LEFT Button
                ${pos}=    Walk Pointer From ${pos} To ${template_path}/drag_and_drop_dst.png
                Release LEFT Button
                Walk Pointer From ${pos} To ${template_path}/drag_and_drop_end.png
        """
        )

        robot = server_instance.program(WaylandRobot(request, robot_test_case))

        async with server_instance, program, robot:
            await robot.wait(60)
            assert program.is_running()
            await program.kill()
        assert "drag-begin\ndrag-failed\nenter-notify-event: dropbox" in program.output
