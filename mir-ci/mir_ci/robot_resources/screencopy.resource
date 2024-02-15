*** Settings ***
Documentation       Keyword definitions for specialised functionality of the Screencopy library.

Library             ../robot_libraries/Screencopy.py
Library             ../robot_libraries/WaylandHid.py


*** Keywords ***
Get Center Of ${region}
    [Documentation]    Get the center point of a region.
    ${point}=    Evaluate
    ...    {"x": (${region}[left] + ${region}[right]) / 2, "y": (${region}[top] + ${region}[bottom]) / 2}
    RETURN    ${point}

Displace ${point} By ${displacement_x} And ${displacement_y}
    [Documentation]    Shift a point by the specified displacements along the x and y axes.
    ${point}=    Evaluate    {"x": ${point}[x] + ${displacement_x}, "y": ${point}[y] + ${displacement_y}}
    RETURN    ${point}

Move Pointer To ${destination}
    [Documentation]    Move the pointer to a position or image template.
    ...
    ...    When ${destination} is the path of an image template file, the pointer
    ...    will move to the center of the first matching template region.
    ...
    ...    The return value is the pointer position after the move.
    IF    ${{isinstance($destination, str)}}
        ${regions}=    Screencopy.Match    ${destination}
        ${position}=    Get Center Of ${regions}[0]
    ELSE
        ${position}=    Set Variable    ${destination}
    END
    WaylandHid.Move Pointer To Absolute    ${position}[x]    ${position}[y]
    RETURN    ${position}

Move Pointer To Proportional ${position}
    [Documentation]    Move the pointer to a position given as proportions to
    ...    the size of the display output.
    ...
    ...    ${position} must be a point represented by floating-point x and y
    ...    values in the range 0..1.
    ...
    ...    The return value is the pointer position after the move,
    ...    in absolute coordinates.
    WaylandHid.Move Pointer To Proportional    ${position}[x]    ${position}[y]
    RETURN    ${position}

Walk Pointer From ${start_position} To ${destination}
    [Documentation]    Move the pointer in incremental steps from a start
    ...    position to a destination position or image template.
    ...
    ...    When ${destination} is the path of an image template file, the
    ...    corresponding position will be that of the center of the first
    ...    matching template region.
    ...
    ...    Optional arguments:
    ...    ${steps}: number of steps. If <= 0, the pointer is moved in
    ...    increments of 16 pixels. Default is 0.
    ...    ${delay}: time to sleep after each step, in seconds.
    ...    Default is 0.
    ...
    ...    The return value is the pointer position after the walk.
    [Arguments]    ${steps}=0    ${delay}=0
    IF    ${{isinstance($destination, str)}}
        ${regions}=    Screencopy.Match    ${destination}
        ${end_position}=    Get Center Of ${regions}[0]
    ELSE
        ${end_position}=    Set Variable    ${destination}
    END
    IF    ${steps} <= 0
        ${distance}=    Distance From ${start_position} To ${end_position}
        ${step_in_pixels}=    Evaluate    16
        ${steps}=    Evaluate    int(${distance} / ${step_in_pixels} + 0.5)
    END
    FOR    ${step}    IN RANGE    0    ${{${steps} + 1}}
        ${t}=    Evaluate    ${step}/${steps}
        ${position}=    Lerp Between ${start_position} And ${end_position} With Parameter ${t}
        WaylandHid.Move Pointer To Absolute    ${position}[x]    ${position}[y]
        Sleep    ${delay}
    END
    RETURN    ${end_position}

Walk Pointer From ${start_position} To Proportional ${end_position}
    [Documentation]    Same as `Walk Pointer From ... To ...`,
    ...    but with a proportional position as destination.
    [Arguments]    ${steps}=0    ${delay}=0
    ${end_position}=    WaylandHid.Get Absolute From Proportional    ${end_position}[x]    ${end_position}[y]
    ${end_position}=    Walk Pointer From ${start_position} To ${end_position}    ${steps}    ${delay}
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
