from pathlib import Path

from mir_ci import apps
from mir_ci.screencopy_tracker import ScreencopyTracker
from mir_ci.virtual_pointer import VirtualPointer

MIR_CI_PATH = Path(__file__).parent
ROBOT_RESOURCES = MIR_CI_PATH / "robot_resources"

ROBOT_TEMPLATE = """\
*** Settings ***
{settings}

*** Variables ***
{variables}

*** Test Cases ***
{test_cases}
"""

WAYLAND_SETTINGS = f"Resource   {ROBOT_RESOURCES}/screencopy.resource"
WAYLAND_VARIABLES = f"${{template_path}}=    {MIR_CI_PATH}/robot_templates"


class Robot(apps.App):
    def __init__(self, request, test_cases, settings="", variables=""):
        tmp_path = request.getfixturevalue("tmp_path")
        procedure = tmp_path / f"{request.node.name}.robot"
        with open(procedure, "w") as f:
            f.write(ROBOT_TEMPLATE.format(test_cases=test_cases, settings=settings, variables=variables))
        super().__init__(("robot", "--outputdir", tmp_path, procedure))


class WaylandRobot(Robot):
    required_extensions = VirtualPointer.required_extensions + ScreencopyTracker.required_extensions

    def __init__(self, request, test_cases, settings="", variables=""):
        super().__init__(request, test_cases, f"{WAYLAND_SETTINGS}\n{settings}", f"{WAYLAND_VARIABLES}\n{variables}")
