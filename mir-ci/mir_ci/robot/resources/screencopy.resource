*** Settings ***
Library    ../libraries/Screencopy.py


*** Keywords ***
Get Center
    [Arguments]    ${region}
    ${center}=    Evaluate    {"x": int((${region}[left] + ${region}[right]) / 2), "y": int((${region}[top] + ${region}[bottom]) / 2)}
    RETURN    ${center}
