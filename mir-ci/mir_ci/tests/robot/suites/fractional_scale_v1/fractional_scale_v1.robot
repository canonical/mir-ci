*** Settings ***
Resource        ${KVM_RESOURCE}

*** Variables ***
${T}    ${CURDIR}

*** Test Cases ***
Click Button With Fractional Scaling Enabled
    Set Output Scale 		${SCALE}
    Move Pointer To Proportional (0.5, 0.5)
    Match                   	${T}/${SCALE}-gtk4-demo-title-app-title.png
    Move Pointer To ${T}/${SCALE}-gtk4-demo-button-combo-boxes.png
    Click LEFT Button
    Match			${T}/${SCALE}-gtk4-demo-title-combo-boxes.png
