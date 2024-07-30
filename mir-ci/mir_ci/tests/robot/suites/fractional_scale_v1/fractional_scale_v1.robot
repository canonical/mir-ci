*** Settings ***
Resource        ${KVM_RESOURCE}

*** Variables ***
${T}    ${CURDIR}

*** Test Cases ***
Click Button With Fractional Scaling Enabled
    Log to console          ${KVM_RESOURCE}
    Match                   ${T}/gtk4-demo-title-app-title.png
    Move Pointer To         ${T}/gtk4-demo-button-simple-constraints.png
    Click LEFT Button
    Match                   ${T}/gtk-4-demo-title-simple-constraints.png

