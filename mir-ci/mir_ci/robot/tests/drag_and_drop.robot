*** Settings ***
Documentation    Test suite for drag and drop

Library          ../libraries/WaylandHid.py    %{WAYLAND_DISPLAY=0}
Resource         ../resources/variables.resource
Test Setup       Connect
Test Teardown    Disconnect

*** Variables ***
${STARTUP_TIME}    ${{1.5 * ${SLOWDOWN}}}
${A_SHORT_TIME}    ${{0.3}}

*** Test Cases ***
Drag And Drop Match
    [Documentation]    Tests drag-and-drop matches
    [Tags]    match

    Sleep     ${STARTUP_TIME}
    Move Pointer To Absolute    40    40
    Sleep     ${A_SHORT_TIME}
    Press LEFT Button
    Sleep     ${A_SHORT_TIME}
    Move Pointer To Absolute    120    70
    Sleep     ${A_SHORT_TIME}
    Move Pointer To Absolute    200    100
    Sleep     ${A_SHORT_TIME}
    Release LEFT Button

Drag And Drop Mismatch
    [Documentation]    Tests drag-and-drop mismatches
    [Tags]    mismatch

    Sleep     ${STARTUP_TIME}
    Move Pointer To Absolute    40    40
    Sleep     ${A_SHORT_TIME}
    Press LEFT Button
    Sleep     ${A_SHORT_TIME}
    Move Pointer To Absolute    120    70
    Sleep     ${A_SHORT_TIME}
    Move Pointer To Absolute    200    100
    Sleep     ${A_SHORT_TIME}
    Release LEFT Button
    Sleep     ${A_SHORT_TIME}
    Move Pointer To Absolute    220    120
    Sleep     ${A_SHORT_TIME}
