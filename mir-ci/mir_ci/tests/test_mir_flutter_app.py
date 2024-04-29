import tempfile
from pathlib import Path
from textwrap import dedent

import pytest
from mir_ci.fixtures.servers import ServerCap, servers
from mir_ci.program.app import App
from mir_ci.program.display_server import DisplayServer
from mir_ci.wayland.screencopy_tracker import ScreencopyTracker
from mir_ci.wayland.virtual_pointer import VirtualPointer

TESTS_PATH = Path(__file__).parent
ASSETS_PATH = TESTS_PATH / "robot/suites/mir_flutter_app"

ROBOT_TEMPLATE = """\
*** Settings ***
{settings}

*** Variables ***
{variables}

*** Keywords ***
{keywords}

*** Test Cases ***
{test_cases}
"""
ROBOT_SETTINGS = f"""\
Library     {TESTS_PATH}/robot/platforms/wayland/Screencopy.py    AS    VIDEO
Library     {TESTS_PATH}/robot/platforms/wayland/WaylandHid.py    AS    HID
Resource    {TESTS_PATH}/robot/resources/kvm/kvm.resource
"""

ROBOT_VARIABLES = f"""\
${{BUTTON_REGULAR}}                           {ASSETS_PATH}/button_regular.png
${{BUTTON_FLOATING_REGULAR}}                  {ASSETS_PATH}/button_floating_regular.png
${{BUTTON_DIALOG}}                            {ASSETS_PATH}/button_dialog.png
${{BUTTON_DIALOG_0}}                          {ASSETS_PATH}/button_dialog_0.png
${{BUTTON_SATELLITE_0}}                       {ASSETS_PATH}/button_satellite_0.png
${{BUTTON_POPUP_0}}                           {ASSETS_PATH}/button_popup_0.png
${{BUTTON_TIP_0}}                             {ASSETS_PATH}/button_tip_0.png
${{BUTTON_CLOSE_FOCUSED}}                     {ASSETS_PATH}/button_close_focused.png
${{BUTTON_CUSTOM_PRESET}}                     {ASSETS_PATH}/button_custom_preset.png
${{BUTTON_SET_DEFAULTS}}                      {ASSETS_PATH}/button_set_defaults.png
${{BUTTON_APPLY}}                             {ASSETS_PATH}/button_apply.png

${{DROPDOWN_PRESET_LABEL}}                    {ASSETS_PATH}/dropdown_preset_label.png
${{DROPDOWN_OPTION_CUSTOM}}                   {ASSETS_PATH}/dropdown_option_custom.png
${{DROPDOWN_OPTION_LEFT}}                     {ASSETS_PATH}/dropdown_option_left.png
${{DROPDOWN_PARENT_ANCHOR_LABEL}}             {ASSETS_PATH}/dropdown_parent_anchor_label.png
${{DROPDOWN_CHILD_ANCHOR_LABEL}}              {ASSETS_PATH}/dropdown_child_anchor_label.png

${{GROUP_NEW_WINDOW}}                         {ASSETS_PATH}/group_new_window.png

${{LABEL_CONSTRAINTS}}                        {ASSETS_PATH}/label_constraints.png

${{WINDOW_MAIN}}                              {ASSETS_PATH}/window_main.png
${{WINDOW_REGULAR_0_FOCUSED}}                 {ASSETS_PATH}/window_regular_0_focused.png
${{WINDOW_FLOATING_REGULAR_0_FOCUSED}}        {ASSETS_PATH}/window_floating_regular_0_focused.png
${{WINDOW_FLOATING_REGULAR_0_NON_FOCUSED}}    {ASSETS_PATH}/window_floating_regular_0_non_focused.png
${{WINDOW_DIALOG_FOCUSED}}                    {ASSETS_PATH}/window_dialog_focused.png
${{WINDOW_SATELLITE_1}}                       {ASSETS_PATH}/window_satellite_1.png
${{WINDOW_POPUP_1}}                           {ASSETS_PATH}/window_popup_1.png
${{WINDOW_TIP_1}}                             {ASSETS_PATH}/window_tip_1.png

${{EXPECTED_SATELLITE_PLACEMENT}}             {ASSETS_PATH}/expected_satellite_placement.png
${{EXPECTED_WINDOW_BEFORE_MOVE}}              {ASSETS_PATH}/expected_window_before_move.png
${{EXPECTED_WINDOW_AFTER_MOVE}}               {ASSETS_PATH}/expected_window_after_move.png
${{EXPECTED_POPUP_PLACEMENT_SLIDE}}           {ASSETS_PATH}/expected_popup_placement_slide.png
${{EXPECTED_POPUP_PLACEMENT_FLIP}}            {ASSETS_PATH}/expected_popup_placement_flip.png
${{EXPECTED_POPUP_PLACEMENT_RESIZE}}          {ASSETS_PATH}/expected_popup_placement_resize.png

${{VERTICAL_DISTANCE_BETWEEN_OPTIONS}}        48
"""

ROBOT_KEYWORDS = """\
Click And Sleep
    Click LEFT Button
    Sleep    0.5

Close Focused Toplevel Window
    Walk Pointer To ${BUTTON_CLOSE_FOCUSED}
    Click And Sleep

Close Dialog
    ${pos}=    Walk Pointer To ${WINDOW_DIALOG_FOCUSED}
    ${pos}=    Displace ${pos} By (112, 0)
    Walk Pointer To ${pos}
    Click And Sleep

Select ${preset} Positioner Preset
    # Reset first to make sure the dropdown list is positioned as expected
    ${pos}=    Move Pointer To ${DROPDOWN_PRESET_LABEL}
    ${pos}=    Displace ${pos} By (0, 20)
    Walk Pointer To ${pos}
    Click And Sleep
    ${pos}=    Displace ${pos} By (0, -${VERTICAL_DISTANCE_BETWEEN_OPTIONS})
    Walk Pointer To ${pos}
    Click And Sleep

    # Select preset
    ${pos}=    Move Pointer To ${DROPDOWN_PRESET_LABEL}
    ${pos}=    Displace ${pos} By (0, 25)
    Walk Pointer To ${pos}
    Click And Sleep
    IF    $preset == "LEFT"
        ${pos}=    Displace ${pos} By (0, ${VERTICAL_DISTANCE_BETWEEN_OPTIONS} * -5)
    ELSE IF    $preset == "RIGHT"
        ${pos}=    Displace ${pos} By (0, ${VERTICAL_DISTANCE_BETWEEN_OPTIONS} * -4)
    ELSE IF    $preset == "BOTTOM_LEFT"
        ${pos}=    Displace ${pos} By (0, ${VERTICAL_DISTANCE_BETWEEN_OPTIONS} * -3)
    ELSE IF    $preset == "BOTTOM"
        ${pos}=    Displace ${pos} By (0, ${VERTICAL_DISTANCE_BETWEEN_OPTIONS} * -2)
    ELSE IF    $preset == "BOTTOM_RIGHT"
        ${pos}=    Displace ${pos} By (0, ${VERTICAL_DISTANCE_BETWEEN_OPTIONS} * -1)
    ELSE IF    $preset == "CENTER"
        ${pos}=    Displace ${pos} By (0, ${VERTICAL_DISTANCE_BETWEEN_OPTIONS} * 0)
    ELSE IF    $preset == "CUSTOM"
        ${pos}=    Displace ${pos} By (0, ${VERTICAL_DISTANCE_BETWEEN_OPTIONS} * 1)
    ELSE
        Fail    Unexpected preset: ${preset}
    END
    Walk Pointer To ${pos}
    Click And Sleep

Move Main Window To The Top Left Of The Output
    ${pos}=    Move Pointer To ${GROUP_NEW_WINDOW}
    ${pos}=    Displace ${pos} By (0, -77)
    Walk Pointer To ${pos}
    Press LEFT Button
    Walk Pointer To (600, 0)
    Release LEFT Button

Set Top Left Custom Positioner
    Move Pointer To ${BUTTON_CUSTOM_PRESET}
    Click And Sleep
    Walk Pointer To ${BUTTON_SET_DEFAULTS}
    Click And Sleep
    # Set parent anchor to 'topLeft'
    ${pos}=    Walk Pointer To ${DROPDOWN_PARENT_ANCHOR_LABEL}
    Click And Sleep
    ${pos}=    Displace ${pos} By (0, ${VERTICAL_DISTANCE_BETWEEN_OPTIONS} * 4)
    Walk Pointer To ${pos}
    Click And Sleep
    # Set child anchor to 'bottomRight'
    ${pos}=    Walk Pointer To ${DROPDOWN_CHILD_ANCHOR_LABEL}
    Click And Sleep
    ${pos}=    Displace ${pos} By (0, ${VERTICAL_DISTANCE_BETWEEN_OPTIONS} * 5)
    Walk Pointer To ${pos}
    Click And Sleep
    Walk Pointer To ${BUTTON_APPLY}
    Click And Sleep
"""


@pytest.mark.parametrize("server", servers(ServerCap.MIR_FLUTTER_APP))
@pytest.mark.deps(
    pip_pkgs=(
        ("robotframework~=6.1.1", "robot"),
        ("rpaframework", "RPA"),
        ("rpaframework-recognition", "RPA.recognition"),
    ),
)
class TestMirFlutterApp:
    async def test_mir_flutter_app(self, robot_log, server, tmp_path) -> None:
        extensions = VirtualPointer.required_extensions + ScreencopyTracker.required_extensions
        server_instance = DisplayServer(server, add_extensions=extensions)

        robot_test_cases = dedent(
            """\
            Reference App Opens
                Sleep    2
                VIDEO.Match    ${WINDOW_MAIN}

            Regular Window Opens
                Move Pointer To ${BUTTON_REGULAR}
                Click And Sleep
                VIDEO.Match    ${WINDOW_REGULAR_0_FOCUSED}
                Close Focused Toplevel Window

            Floating Regular Window Opens
                Move Pointer To ${BUTTON_FLOATING_REGULAR}
                Click And Sleep
                VIDEO.Match    ${WINDOW_FLOATING_REGULAR_0_FOCUSED}
                Close Focused Toplevel Window

            Dialog Window Opens
                Move Pointer To ${BUTTON_DIALOG}
                Click And Sleep
                VIDEO.Match    ${WINDOW_DIALOG_FOCUSED}
                Close Focused Toplevel Window

            Satellite Window Opens
                Move Pointer To ${BUTTON_REGULAR}
                Click And Sleep
                Walk Pointer To ${BUTTON_SATELLITE_0}
                Click And Sleep
                Walk Pointer To ${WINDOW_SATELLITE_1}
                Click And Sleep
                Close Focused Toplevel Window

            Popup Window Opens
                Move Pointer To ${BUTTON_REGULAR}
                Click And Sleep
                Walk Pointer To ${BUTTON_POPUP_0}
                Click And Sleep
                Walk Pointer to ${WINDOW_POPUP_1}
                Click And Sleep
                Close Focused Toplevel Window

            Tip Window Opens
                Move Pointer To ${BUTTON_REGULAR}
                Click And Sleep
                Walk Pointer To ${BUTTON_TIP_0}
                Click And Sleep
                Walk Pointer to ${WINDOW_TIP_1}
                Click And Sleep
                Close Focused Toplevel Window

            Floating Regular Window Stays On Top
                Move Pointer To ${BUTTON_FLOATING_REGULAR}
                Click And Sleep
                Walk Pointer To ${GROUP_NEW_WINDOW}
                Click And Sleep
                Walk Pointer To ${WINDOW_FLOATING_REGULAR_0_NON_FOCUSED}
                Click And Sleep
                Close Focused Toplevel Window

            Dialog Is Modal To Parent
                Move Pointer To ${BUTTON_REGULAR}
                Click And Sleep
                Walk Pointer To ${BUTTON_DIALOG_0}
                Click And Sleep
                # Try to close parent
                ${pos}=    Walk Pointer To ${WINDOW_REGULAR_0_FOCUSED}
                ${pos}=    Displace ${pos} By (130, 0)
                Walk Pointer To ${pos}
                Click And Sleep
                # Expect parent to be still open
                VIDEO.Match    ${WINDOW_REGULAR_0_FOCUSED}
                Close Dialog
                Close Focused Toplevel Window

            Satellite Is Placed According To Custom Positioner
                Select CUSTOM Positioner Preset
                Walk Pointer To ${BUTTON_FLOATING_REGULAR}
                Click And Sleep
                Walk Pointer To ${BUTTON_SATELLITE_0}
                Click And Sleep
                VIDEO.Match    ${EXPECTED_SATELLITE_PLACEMENT}
                Close Focused Toplevel Window

            Child Windows Move With Parent
                Move Pointer To ${BUTTON_FLOATING_REGULAR}
                Click And Sleep
                Select LEFT Positioner Preset
                Walk Pointer To ${BUTTON_SATELLITE_0}
                Click And Sleep
                Select BOTTOM_LEFT Positioner Preset
                Walk Pointer To ${BUTTON_POPUP_0}
                Click And Sleep
                Select BOTTOM Positioner Preset
                Walk Pointer To ${BUTTON_TIP_0}
                Click And Sleep
                Select CENTER Positioner Preset
                Walk Pointer To ${BUTTON_DIALOG_0}
                Click And Sleep
                ${pos}=    Walk Pointer To ${WINDOW_FLOATING_REGULAR_0_FOCUSED}
                Press LEFT Button
                VIDEO.Match    ${EXPECTED_WINDOW_BEFORE_MOVE}
                ${pos}=    Displace ${pos} By (50, 25)
                Walk Pointer To ${pos}
                Release LEFT Button
                VIDEO.Match    ${EXPECTED_WINDOW_AFTER_MOVE}
                Close Dialog
                Close Focused Toplevel Window

            Slide Constraint Is Applied
                Set Top Left Custom Positioner
                Move Main Window To The Top Left Of The Output
                Walk Pointer To ${BUTTON_FLOATING_REGULAR}
                Click And Sleep
                Walk Pointer To ${WINDOW_FLOATING_REGULAR_0_FOCUSED}
                Press LEFT Button
                Walk Pointer To (250, 90)
                Release LEFT Button
                Walk Pointer To ${BUTTON_POPUP_0}
                Click And Sleep
                VIDEO.Match    ${EXPECTED_POPUP_PLACEMENT_SLIDE}
                Close Focused Toplevel Window

            Flip Constraint Is Applied
                Set Top Left Custom Positioner
                Move Pointer To ${BUTTON_CUSTOM_PRESET}
                Click And Sleep
                ${pos}=    Walk Pointer To ${LABEL_CONSTRAINTS}
                # Uncheck 'slide X' checkbox
                ${pos}=    Displace ${pos} By (100, -30)
                Walk Pointer To ${pos}
                Click And Sleep
                # Uncheck 'slide Y' checkbox
                ${pos}=    Walk Pointer To ${LABEL_CONSTRAINTS}
                ${pos}=    Displace ${pos} By (170, -30)
                Walk Pointer To ${pos}
                Click And Sleep
                # Check 'flip X' checkbox
                ${pos}=    Walk Pointer To ${LABEL_CONSTRAINTS}
                ${pos}=    Displace ${pos} By (100, 0)
                Walk Pointer To ${pos}
                Click And Sleep
                # Check 'flip Y' checkbox
                ${pos}=    Walk Pointer To ${LABEL_CONSTRAINTS}
                ${pos}=    Displace ${pos} By (170, 0)
                Walk Pointer To ${pos}
                Click And Sleep
                Walk Pointer To ${BUTTON_APPLY}
                Click And Sleep
                Move Main Window To The Top Left Of The Output
                Walk Pointer To ${BUTTON_FLOATING_REGULAR}
                Click And Sleep
                Walk Pointer To ${WINDOW_FLOATING_REGULAR_0_FOCUSED}
                Press LEFT Button
                Walk Pointer To (250, 90)
                Release LEFT Button
                Walk Pointer To ${BUTTON_POPUP_0}
                Click And Sleep
                VIDEO.Match    ${EXPECTED_POPUP_PLACEMENT_FLIP}
                Close Focused Toplevel Window

            Resize Constraint Is Applied
                Set Top Left Custom Positioner
                Move Pointer To ${BUTTON_CUSTOM_PRESET}
                Click And Sleep
                ${pos}=    Walk Pointer To ${LABEL_CONSTRAINTS}
                # Uncheck 'slide X' checkbox
                ${pos}=    Displace ${pos} By (100, -30)
                Walk Pointer To ${pos}
                Click And Sleep
                # Uncheck 'slide Y' checkbox
                ${pos}=    Walk Pointer To ${LABEL_CONSTRAINTS}
                ${pos}=    Displace ${pos} By (170, -30)
                Walk Pointer To ${pos}
                Click And Sleep
                # Check 'resize X' checkbox
                ${pos}=    Walk Pointer To ${LABEL_CONSTRAINTS}
                ${pos}=    Displace ${pos} By (100, 30)
                Walk Pointer To ${pos}
                Click And Sleep
                # Check 'resize Y' checkbox
                ${pos}=    Walk Pointer To ${LABEL_CONSTRAINTS}
                ${pos}=    Displace ${pos} By (170, 30)
                Walk Pointer To ${pos}
                Click And Sleep
                Walk Pointer To ${BUTTON_APPLY}
                Click And Sleep
                Move Main Window To The Top Left Of The Output
                Walk Pointer To ${BUTTON_FLOATING_REGULAR}
                Click And Sleep
                Walk Pointer To ${WINDOW_FLOATING_REGULAR_0_FOCUSED}
                Press LEFT Button
                Walk Pointer To (250, 60)
                Release LEFT Button
                Walk Pointer To ${BUTTON_POPUP_0}
                Click And Sleep
                VIDEO.Match    ${EXPECTED_POPUP_PLACEMENT_RESIZE}
                Close Focused Toplevel Window

            Flip Constraint Precedes Slide
                Set Top Left Custom Positioner
                Move Pointer To ${BUTTON_CUSTOM_PRESET}
                Click And Sleep
                # Check 'flip X' checkbox
                ${pos}=    Walk Pointer To ${LABEL_CONSTRAINTS}
                ${pos}=    Displace ${pos} By (100, 0)
                Walk Pointer To ${pos}
                Click And Sleep
                # Check 'flip Y' checkbox
                ${pos}=    Walk Pointer To ${LABEL_CONSTRAINTS}
                ${pos}=    Displace ${pos} By (170, 0)
                Walk Pointer To ${pos}
                Click And Sleep
                Walk Pointer To ${BUTTON_APPLY}
                Click And Sleep
                Move Main Window To The Top Left Of The Output
                Walk Pointer To ${BUTTON_FLOATING_REGULAR}
                Click And Sleep
                Walk Pointer To ${WINDOW_FLOATING_REGULAR_0_FOCUSED}
                Press LEFT Button
                Walk Pointer To (250, 90)
                Release LEFT Button
                Walk Pointer To ${BUTTON_POPUP_0}
                Click And Sleep
                VIDEO.Match    ${EXPECTED_POPUP_PLACEMENT_FLIP}
                Close Focused Toplevel Window

            Slide Constraint Precedes Resize
                Set Top Left Custom Positioner
                Move Pointer To ${BUTTON_CUSTOM_PRESET}
                Click And Sleep
                # Check 'resize X' checkbox
                ${pos}=    Walk Pointer To ${LABEL_CONSTRAINTS}
                ${pos}=    Displace ${pos} By (100, 30)
                Walk Pointer To ${pos}
                Click And Sleep
                # Check 'resize Y' checkbox
                ${pos}=    Walk Pointer To ${LABEL_CONSTRAINTS}
                ${pos}=    Displace ${pos} By (170, 30)
                Walk Pointer To ${pos}
                Click And Sleep
                Walk Pointer To ${BUTTON_APPLY}
                Click And Sleep
                Move Main Window To The Top Left Of The Output
                Walk Pointer To ${BUTTON_FLOATING_REGULAR}
                Click And Sleep
                Walk Pointer To ${WINDOW_FLOATING_REGULAR_0_FOCUSED}
                Press LEFT Button
                Walk Pointer To (250, 90)
                Release LEFT Button
                Walk Pointer To ${BUTTON_POPUP_0}
                Click And Sleep
                VIDEO.Match    ${EXPECTED_POPUP_PLACEMENT_SLIDE}
                Close Focused Toplevel Window
        """
        )

        async with server_instance:
            with tempfile.NamedTemporaryFile(mode="w+", suffix=".robot", buffering=1) as robot_file:
                robot_file.write(
                    ROBOT_TEMPLATE.format(
                        settings=ROBOT_SETTINGS,
                        variables=ROBOT_VARIABLES,
                        keywords=ROBOT_KEYWORDS,
                        test_cases=robot_test_cases,
                    )
                )
                robot = server_instance.program(App(("robot", "-d", tmp_path, "--log", robot_log, robot_file.name)))

                async with robot:
                    await robot.wait(120)
