*** Settings ***
Documentation       Keyword definitions for specialised functionality
...                 of the Screencopy library.

Library             ../robot_libraries/Screencopy.py
Library             ../robot_libraries/WaylandHid.py


*** Keywords ***
Get Center Of ${region}
    [Documentation]    Get the center point of a region.
    ...
    ...    The return value is a tuple (x, y) of integers.
    ${point}=    Evaluate
    ...    (int((${region}[left] + ${region}[right]) / 2), int((${region}[top] + ${region}[bottom]) / 2))
    RETURN    ${point}

Displace ${point} By (${x}, ${y})
    [Documentation]    Shift a point by the specified displacements along
    ...    the x and y axes.
    ...
    ...    ${point} must be a tuple (x, y).
    ...
    ...    The return value is the displaced point, represented as a tuple
    ...    (x, y) of integers.
    ${point}=    Evaluate    (int(${point}[0] + ${x}), int(${point}[1] + ${y}))
    RETURN    ${point}

Move Pointer To ${destination:^\(?!\(.+,.+\)\).+}
    [Documentation]    Move the pointer to an absolute position or image
    ...    template.
    ...
    ...    If ${destination} is a tuple (x, y), the pointer will move to
    ...    the corresponding absolute position. Otherwise,
    ...    if ${destination} is the path of an image template file, the
    ...    pointer will move to the center of the first matching template
    ...    region.
    ...
    ...    The return value is the absolute position of the pointer after
    ...    the move, represented as a tuple (x, y) of integers.
    IF    ${{isinstance($destination, str)}}
        ${regions}=    Screencopy.Match    ${destination}
        ${position}=    Get Center Of ${regions}[0]
    ELSE
        ${position}=    Set Variable    ${destination}
    END
    WaylandHid.Move Pointer To (${position}[0], ${position}[1])
    RETURN    ${position}

Walk Pointer To (${x}, ${y})
    [Documentation]    Move the pointer in incremental steps from the
    ...    current pointer position to an absolute position.
    ...
    ...    Optional arguments:
    ...    ${steps}: number of steps. If <= 0, the pointer is moved in
    ...    increments of 16 pixels. Default is 0.
    ...    ${delay}: time to sleep after each step, in seconds.
    ...    Default is 0.01.
    [Arguments]    ${steps}=0    ${delay}=0.01
    WaylandHid.Walk Pointer To Absolute    ${x}    ${y}    ${steps}    ${delay}

Walk Pointer To ${destination:^\(?!\(.+,.+\)\).+}
    [Documentation]    Moves the pointer in incremental steps from the
    ...    current pointer position to an absolute position or image
    ...    template.
    ...
    ...    If ${destination} is a tuple (x, y), the pointer will move to
    ...    the corresponding absolute position. Otherwise,
    ...    if ${destination} is the path of an image template file, the
    ...    pointer will move to the center of the first matching template
    ...    region.
    ...
    ...    Optional arguments:
    ...    ${steps}: number of steps. If <= 0, the pointer is moved in
    ...    increments of 16 pixels. Default is 0.
    ...    ${delay}: time to sleep after each step, in seconds.
    ...    Default is 0.01.
    ...
    ...    The return value is the absolute position of the pointer after
    ...    the walk, represented as a tuple (x, y) of integers.
    [Arguments]    ${steps}=0    ${delay}=0.01
    IF    ${{isinstance($destination, str)}}
        ${regions}=    Screencopy.Match    ${destination}
        ${position}=    Get Center Of ${regions}[0]
    ELSE
        ${position}=    Set Variable    ${destination}
    END
    WaylandHid.Walk Pointer To Absolute    ${position}[0]    ${position}[1]    ${steps}    ${delay}
    RETURN    ${position}

Walk Pointer To Proportional (${x}, ${y})
    [Documentation]    Move the pointer in incremental steps from the
    ...    current pointer position to a destination position given as
    ...    proportions to the size of the display output. The proportions
    ...    must be in the range 0..1.
    ...
    ...    Optional arguments:
    ...    ${steps}: number of steps. If <= 0, the pointer is moved in
    ...    increments of 16 pixels. Default is 0.
    ...    ${delay}: time to sleep after each step, in seconds.
    ...    Default is 0.01.
    ...
    ...    The return value is the absolute position of the pointer after
    ...    the walk, represented as a tuple (x, y) of integers.
    [Arguments]    ${steps}=0    ${delay}=0.01
    WaylandHid.Walk Pointer To Proportional    ${x}    ${y}    ${steps}    ${delay}
    ${position}=    WaylandHid.Get Absolute From Proportional    ${x}    ${y}
    RETURN    ${position}
