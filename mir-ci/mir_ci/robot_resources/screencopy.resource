*** Settings ***
Documentation       Keyword definitions for specialised functionality of the Screencopy library.

Library             ../robot_libraries/Screencopy.py
Library             ../robot_libraries/WaylandHid.py


*** Keywords ***
Get Center
    [Documentation]    Get the center point of a region.
    [Arguments]    ${region}
    ${point}=    Evaluate
    ...    {"x": int((${region}[left] + ${region}[right]) / 2), "y": int((${region}[top] + ${region}[bottom]) / 2)}
    RETURN    ${point}

Displace
    [Documentation]    Shift a point by the specified displacements along the x and y axes.
    [Arguments]    ${point}    ${displacement_x}    ${displacement_y}
    ${point}=    Evaluate    {"x": ${point}[x] + ${displacement_x}, "y": ${point}[y] + ${displacement_y}}
    RETURN    ${point}

Move Pointer To Template
    [Documentation]    Move the pointer to the center of the first matching image template.
    [Arguments]    ${template}
    ${regions}=    Match    ${template}
    ${center}=    Get Center    ${regions}[0]
    Move Pointer To Absolute    ${center}[x]    ${center}[y]
    RETURN    ${center}

Walk Pointer From ${start_position} To Template
    [Documentation]    Move the pointer in incremental steps from a start position
    ...    to the center of the first matching image template.
    ...    If ${steps} <= 0, the pointer is moved in increments of 16 pixels.
    ...    ${step_sleep} is the time to sleep after each step, in seconds.
    ...    The return value is the pointer position after the walk.
    [Arguments]    ${template}    ${steps}=0    ${step_sleep}=0
    ${regions}=    Match    ${template}
    ${end_position}=    Get Center    ${regions}[0]
    IF    ${steps} <= 0
        ${distance}=    Distance From ${start_position} To ${end_position}
        ${step_in_pixels}=    Evaluate    16
        ${steps}=    Evaluate    int(${distance} / ${step_in_pixels} + 0.5)
    END
    FOR    ${step}    IN RANGE    0    ${{${steps} + 1}}
        ${t}=    Evaluate    ${step}/${steps}
        ${point}=    Lerp Between ${start_position} And ${end_position} With Parameter ${t}
        Move Pointer To Absolute    ${point}[x]    ${point}[y]
        Sleep    ${step_sleep}
    END
    RETURN    ${end_position}

Distance From ${point_a} To ${point_b}
    [Documentation]    Calculate the Euclidean distance between two points.
    ${distance}=    Evaluate    ((${point_b}[x] - ${point_a}[x]) ** 2 + (${point_b}[y] - ${point_a}[y]) ** 2) ** 0.5
    RETURN    ${distance}

Lerp Between ${point_a} And ${point_b} With Parameter ${t}
    [Documentation]    Calculate the linear interpolation between two points with a parameter t.
    ${point}=    Evaluate
    ...    {"x": (1-${t})*${point_a}[x]+${t}*${point_b}[x], "y": (1-${t})*${point_a}[y]+${t}*${point_b}[y]}
    RETURN    ${point}
