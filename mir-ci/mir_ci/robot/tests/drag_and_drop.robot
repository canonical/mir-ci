*** Settings ***
Documentation    Test suite for drag and drop match

Library       ../libraries/VirtualPointer.py    %{WAYLAND_DISPLAY=0}
Resource      ../resources/variables.resource
Test Setup    Connect to Display

*** Variables ***
${STARTUP_TIME}    ${{1.5 * ${SLOWDOWN}}}
${A_SHORT_TIME}    ${{0.3}}

*** Test Cases ***
Drag And Drop Match
    [Documentation]    Tests drag-and-drop matches
    [Tags]    match

    Sleep     ${STARTUP_TIME}
    Move To Absolute    40    40
    Sleep     ${A_SHORT_TIME}
    Button    ${LEFT}    True
    Sleep     ${A_SHORT_TIME}
    Move To Absolute    120    70
    Sleep     ${A_SHORT_TIME}
    Move To Absolute    200    100
    Sleep     ${A_SHORT_TIME}
    Button    ${LEFT}    False

Drag And Drop Mismatch
    [Documentation]    Tests drag-and-drop mismatches
    [Tags]    mismatch

    Sleep     ${STARTUP_TIME}
    Move To Absolute    40    40
    Sleep     ${A_SHORT_TIME}
    Button    ${LEFT}    True
    Sleep     ${A_SHORT_TIME}
    Move To Absolute    120    70
    Sleep     ${A_SHORT_TIME}
    Move To Absolute    200    100
    Sleep     ${A_SHORT_TIME}
    Button    ${LEFT}    False
    Sleep     ${A_SHORT_TIME}
    Move To Absolute    220    120
    Sleep     ${A_SHORT_TIME}
