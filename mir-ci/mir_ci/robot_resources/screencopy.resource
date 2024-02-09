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
    [Documentation]    Move the pointer to a point position or image template.
    ...
    ...    If ${destination} is an image template, the corresponding position
    ...    will be that of the center of the first matching template region.
    ...
    ...    Optional arguments:
    ...    ${proportional}: if True, coordinates in ${destination} are
    ...    considered as proportions to the output dimensions. This argument
    ...    is ignored if ${destination} is an image template. Default is False.
    ...
    ...    The return value is the pointer position after the move.
    [Arguments]    ${proportional}=False
    IF    ${{isinstance($destination, str)}}
        ${regions}=    Screencopy.Match    ${destination}
        ${position}=    Get Center Of ${regions}[0]
    ELSE
        IF    ${proportional} == True
            ${position}=    WaylandHid.Get Absolute From Proportional    ${destination}[x]    ${destination}[y]
        ELSE
            ${position}=    Set Variable    ${destination}
        END
    END
    WaylandHid.Move Pointer To Absolute    ${position}[x]    ${position}[y]
    RETURN    ${position}

Walk Pointer From ${source} To ${destination}
    [Documentation]    Move the pointer in incremental steps from a source
    ...    point position or image template to a destination point position
    ...    or image template.
    ...
    ...    If an image template is given as ${source} or ${destination}, the
    ...    corresponding position will be that of the center of the first
    ...    matching template region.
    ...
    ...    Optional arguments:
    ...    ${steps}: number of steps. If <= 0, the pointer is moved in
    ...    increments of 16 pixels. Default is 0.
    ...    ${step_sleep}: time to sleep after each step, in seconds.
    ...    Default is 0.
    ...    ${proportional_source}: if True, coordinates in ${source}
    ...    are considered as proportions to the output dimensions. This
    ...    argument is ignored if ${source} is an image template.
    ...    Default is False.
    ...    ${proportional_destination}: if True, coordinates in ${destination}
    ...    are considered as proportions to the output dimensions. This
    ...    argument is ignored if ${destination} is an image template.
    ...    Default is False.
    ...
    ...    The return value is the pointer position after the walk.
    [Arguments]    ${steps}=0    ${step_sleep}=0    ${proportional_source}=False    ${proportional_destination}=False
    IF    ${{isinstance($source, str)}}
        ${regions}=    Screencopy.Match    ${source}
        ${start_position}=    Get Center Of ${regions}[0]
    ELSE
        IF    ${proportional_source} == True
            ${start_position}=    WaylandHid.Get Absolute From Proportional    ${source}[x]    ${source}[y]
        ELSE
            ${start_position}=    Set Variable    ${source}
        END
    END
    IF    ${{isinstance($destination, str)}}
        ${regions}=    Screencopy.Match    ${destination}
        ${end_position}=    Get Center Of ${regions}[0]
    ELSE
        IF    ${proportional_destination} == True
            ${end_position}=    WaylandHid.Get Absolute From Proportional    ${destination}[x]    ${destination}[y]
        ELSE
            ${end_position}=    Set Variable    ${destination}
        END
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
