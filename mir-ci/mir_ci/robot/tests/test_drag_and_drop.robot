*** Settings ***
Documentation    Test suite for drag and drop

Resource         ../resources/drag_and_drop.resource

*** Test Cases ***
Drag And Drop Match
    [Documentation]    Tests drag-and-drop matches
    [Template]         Test Source And Destination Match
    [Tags]             drag_and_drop

    VAR    @{apps}
    ...    python3 ${APP_PATH} --source pixbuf --target pixbuf --expect pixbuf
    ...    python3 ${APP_PATH} --source text --target text --expect text

    FOR    ${app_index}    ${app}    IN ENUMERATE    @{apps}    start=0
        FOR    ${server}    IN    @{SERVERS}
            ${app_index}    ${app}    ${server}
        END
    END


Drag And Drop Mismatch
    [Documentation]    Tests drag-and-drop mismatches
    [Template]         Test Source And Destination Mismatch
    [Tags]             drag_and_drop

    VAR    @{apps}
    ...    python3 -u ${APP_PATH} --source pixbuf --target text --expect pixbuf
    ...    python3 -u ${APP_PATH} --source text --target pixbuf --expect text
    ...    python3 -u ${APP_PATH} --source pixbuf --target text --expect text
    ...    python3 -u ${APP_PATH} --source text --target pixbuf --expect pixbuf

    FOR    ${app_index}    ${app}    IN ENUMERATE    @{apps}    start=0
        FOR    ${server}    IN    @{SERVERS}
            ${app_index}    ${app}    ${server}
        END
    END
