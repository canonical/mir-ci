*** Keywords ***
Get Center
    [Arguments]    ${region}
    ${point}=    Evaluate
    ...    {"x": int((${region}[left] + ${region}[right]) / 2), "y": int((${region}[top] + ${region}[bottom]) / 2)}
    RETURN    ${point}

Add Displacement
    [Arguments]    ${point}    ${displacement_x}    ${displacement_y}
    ${point}=    Evaluate    {"x": ${point}[x] + ${displacement_x}, "y": ${point}[y] + ${displacement_y}}
    RETURN    ${point}
