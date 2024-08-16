*** Settings ***
Resource        ${KVM_RESOURCE}

Suite Setup     Suite Setup
Test Setup      Set Output Scale    ${SCALE}


*** Variables ***
${T}                        ${CURDIR}
${SCREENSHOT}               ${T}/${SCALE}-gtk4-demo-screenshot.png
${DEMO-APP-TITLE}           ${T}/${SCALE}-gtk4-demo-title-main.png
${DEMO-APP-TITLE-HALF}      ${T}/${SCALE}-gtk4-demo-title-main-half.png
${BUTTON}                   ${T}/${SCALE}-gtk4-demo-button.png
${TITLE}                    ${T}/${SCALE}-gtk4-demo-title.png


*** Test Cases ***
Ensure Scaling Is Visually Correct
    Move Pointer To Proportional (1.0, 1.0)

    Match                   ${SCREENSHOT}

Click Button With Scaling Enabled
    Walk Pointer To ${BUTTON}
    Click LEFT Button

    Match                   ${TITLE}


*** Keywords ***
Suite Setup
    Set Output Scale        ${SCALE}
    # Work around https://github.com/canonical/mir/issues/3553
    ${aligned}=             Run Keyword And Return Status
    ...                     Walk Pointer To ${DEMO-APP-TITLE}
    IF    ${aligned} == False    Walk Pointer To ${DEMO-APP-TITLE-HALF}
    Click LEFT Button
    Click LEFT Button
