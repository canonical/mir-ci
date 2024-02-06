*** Settings ***
Library    ../robot_libraries/Screencopy.py
Library    ../robot_libraries/WaylandHid.py

*** Keywords ***
Get Center
    [Arguments]    ${region}
    ${point}=    Evaluate
    ...    {"x": int((${region}[left] + ${region}[right]) / 2), "y": int((${region}[top] + ${region}[bottom]) / 2)}
    RETURN    ${point}

Displace
    [Arguments]    ${point}    ${displacement_x}    ${displacement_y}
    ${point}=    Evaluate    {"x": ${point}[x] + ${displacement_x}, "y": ${point}[y] + ${displacement_y}}
    RETURN    ${point}

Move Pointer Above Template
    [Arguments]    ${template}
    ${regions} =    Match    ${template}
    ${center} =    Get Center    ${regions}[0]
    Move Pointer To Absolute    ${center}[x]    ${center}[y]
    RETURN    ${center}
