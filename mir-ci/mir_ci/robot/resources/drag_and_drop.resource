*** Settings ***
Library    ../libraries/DragAndDrop.py

*** Variables ***
${APP_PATH}        ${CURDIR}${/}..${/}..${/}clients${/}drag_and_drop_demo.py
${STARTUP_TIME}    ${{1.5 * %{MIR_CI_SLOWDOWN=1}}}
${A_SHORT_TIME}    ${{0.3}}
@{SERVERS}
...    ubuntu_frame
# ...    mir_kiosk    # we need servers based on Mir 2.14 or later
# ...    confined_shell
...    mir_test_tools
...    mir_demo_server

@{APPS_MATCH}
...    python3 ${APP_PATH} --source pixbuf --target pixbuf --expect pixbuf
...    python3 ${APP_PATH} --source text --target text --expect text

@{APPS_MISMATCH}
...    python3 -u ${APP_PATH} --source pixbuf --target text --expect pixbuf
...    python3 -u ${APP_PATH} --source text --target pixbuf --expect text
...    python3 -u ${APP_PATH} --source pixbuf --target text --expect text
...    python3 -u ${APP_PATH} --source text --target pixbuf --expect pixbuf

*** Keywords ***
Test Source And Destination Match
    Log To Console    \n
    FOR    ${app_index}    ${app}    IN ENUMERATE    @{APPS_MATCH}    start=0
        FOR    ${server}    IN    @{SERVERS}
            Log    [app${app_index}-${server}]    console=True
            
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
        END
    END

Test Source And Destination Mismatch
    Log To Console    \n
    FOR    ${app_index}    ${app}    IN ENUMERATE    @{APPS_MISMATCH}    start=0
        FOR    ${server}    IN    @{SERVERS}
            Log    [app${app_index}-${server}]    console=True
            
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
        END
    END
