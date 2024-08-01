*** Settings ***
Resource        ${KVM_RESOURCE}

*** Variables ***
${T}    ${CURDIR}

*** Test Cases ***
Click Button With Fractional Scaling Enabled
    Log to console          ${KVM_RESOURCE}
    Move Pointer To Proportional (0.5, 0.5)
    Match                   	${T}/${SCALE}-gtk4-demo-title-app-title.png
    Move Pointer To ${T}/${SCALE}-gtk4-demo-button-simple-constraints.png
    Click LEFT Button
    Match			${T}/${SCALE}-gtk4-demo-title-simple-constraints.png
