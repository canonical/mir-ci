*** Settings ***
Resource        ${KVM_RESOURCE}

Test Setup 	Set Output Scale	${SCALE}

*** Variables ***
${T}    ${CURDIR}

*** Test Cases ***
Ensure Scaling Is Visually Correct
    Move Pointer To Proportional (1.0, 1.0)
    Match 			${T}/${SCALE}-gtk4-demo-screenshot-floating.png

    Walk Pointer To ${T}/${SCALE}-gtk4-demo-title-app-title.png
    Click LEFT Button
    Click LEFT Button
    Move Pointer To Proportional (1.0, 1.0)

    Match 			${T}/${SCALE}-gtk4-demo-screenshot-maximized.png

    Walk Pointer To ${T}/${SCALE}-gtk4-demo-title-app-title.png
    Click LEFT Button
    Click LEFT Button

Click Button With Fractional Scaling Enabled
    Move Pointer To Proportional (0.5, 0.5)
    Match                   	${T}/${SCALE}-gtk4-demo-title-app-title.png
    Move Pointer To ${T}/${SCALE}-gtk4-demo-button-combo-boxes.png
    Click LEFT Button
    Match			${T}/${SCALE}-gtk4-demo-title-combo-boxes.png
