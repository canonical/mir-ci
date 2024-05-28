import tempfile
from pathlib import Path
from textwrap import dedent

import pytest
from mir_ci.fixtures import apps
from mir_ci.fixtures.servers import ServerCap, servers
from mir_ci.program.app import App
from mir_ci.program.display_server import DisplayServer
from mir_ci.wayland.protocols import ZwlrScreencopyManagerV1, ZwlrVirtualPointerManagerV1

TESTS_PATH = Path(__file__).parent

ROBOT_TEMPLATE = """\
*** Settings ***
{settings}

*** Test Cases ***
{test_case}
"""
ROBOT_SETTINGS = f"""\
Library     {TESTS_PATH}/robot/platforms/vnc/Vnc.py    AS    VIDEO
Library     {TESTS_PATH}/robot/platforms/vnc/Vnc.py    AS    HID
Resource    {TESTS_PATH}/robot/resources/kvm/kvm.resource
"""


@pytest.mark.parametrize("server", servers(ServerCap.VNC))
@pytest.mark.deps(
    debs=("wayvnc",),
    pip_pkgs=(
        ("asyncvnc", "asyncvnc"),
        ("robotframework~=6.1.1", "robot"),
        ("rpaframework", "RPA"),
        ("rpaframework-recognition", "RPA.recognition"),
    ),
)
class TestVnc:
    @pytest.mark.parametrize("app", (apps.qterminal("--execute", "wayvnc"),))
    async def test_vnc(self, robot_log, server, app, tmp_path) -> None:
        extensions = (ZwlrVirtualPointerManagerV1.name, ZwlrScreencopyManagerV1.name, "zwp_virtual_keyboard_manager_v1")
        server_instance = DisplayServer(server, add_extensions=extensions)
        program = server_instance.program(app)

        robot_test_case = dedent(
            """\
            Vnc
                Sleep    1
                HID.Type String    Hello World
                Sleep    1
                # Drag window (assuming a 5:4 aspect ratio output)
                Move Pointer To Proportional (0.5, 0.19)
                Press LEFT Button
                Walk Pointer To Proportional (1, 0.6)
                Release LEFT Button
        """
        )

        with tempfile.NamedTemporaryFile(mode="w+", suffix=".robot", buffering=1) as robot_file:
            robot_file.write(ROBOT_TEMPLATE.format(settings=ROBOT_SETTINGS, test_case=robot_test_case))
            robot = server_instance.program(App(("robot", "-d", tmp_path, "--log", robot_log, robot_file.name)))

            async with server_instance, program:
                async with robot:
                    await robot.wait()
