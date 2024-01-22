*** Settings ***
Library      ../libraries/DragAndDrop.py
Resource    variables.resource

*** Variables ***
${APP_PATH}        ${MIR_CI_DIR}${/}clients${/}drag_and_drop_demo.py
${STARTUP_TIME}    ${{1.5 * ${SLOWDOWN}}}
${A_SHORT_TIME}    ${{0.3}}

@{SERVERS}
...    ubuntu_frame
# ...    mir_kiosk    # we need servers based on Mir 2.14 or later
# ...    confined_shell
...    mir_test_tools
...    mir_demo_server

*** Keywords ***
Test Source And Destination Match
    [Arguments]    ${app_index}    ${app}    ${server}
    [Setup]        Log To Console    [app${app_index}-${server}]
    [Tags]         [app${app_index}-${server}]

    Sleep For    ${STARTUP_TIME}
    Move Pointer To Absolute    40    40
    Press Left Button
    Sleep For    ${A_SHORT_TIME}
    Move Pointer To Absolute    120    70
    Sleep For    ${A_SHORT_TIME}
    Move Pointer To Absolute    200    100
    Sleep For    ${A_SHORT_TIME}
    Release Left Button
    Wait Program

    Run Async   ${server}    ${app}

Test Source And Destination Mismatch
    [Arguments]    ${app_index}    ${app}    ${server}
    [Setup]        Log To Console    [app${app_index}-${server}]
    [Tags]         [app${app_index}-${server}]
        
    Sleep For    ${STARTUP_TIME}
    Move Pointer To Absolute    40    40
    Sleep For    ${A_SHORT_TIME}
    Press Left Button
    Sleep For    ${A_SHORT_TIME}
    Move Pointer To Absolute    120    70
    Sleep For    ${A_SHORT_TIME}
    Move Pointer To Absolute    200    100
    Sleep For    ${A_SHORT_TIME}
    Release Left Button
    Sleep For    ${A_SHORT_TIME}
    Move Pointer To Absolute    220    120
    Sleep For    ${A_SHORT_TIME}
    Assert Program Is Running
    Kill Program

    Run Async    ${server}    ${app}

    ${output}=    Program Output
    Should Contain    ${output}    drag-begin\ndrag-failed\nenter-notify-event: dropbox
