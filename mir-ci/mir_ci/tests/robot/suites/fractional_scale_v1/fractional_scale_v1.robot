*** Settings ***
Resource        ${KVM_RESOURCE}

Test Setup      Set Output Scale    ${SCALE}


*** Variables ***
<<<<<<< HEAD
${T}                ${CURDIR}
${COMBO-BOXES}      ${T}/${SCALE}-gtk4-demo-button-combo-boxes-maximized.png
=======
${T}                        ${CURDIR}
${FLOATING-SCREENSHOT}      ${T}/${SCALE}-gtk4-demo-screenshot-floating.png
${MAXIMIZED-SCREENSHOT}     ${T}/${SCALE}-gtk4-demo-screenshot-maximized.png
${DEMO-APP-TITLE}           ${T}/${SCALE}-gtk4-demo-title-app-title.png
${DEMO-APP-TITLE-HALF}      ${T}/${SCALE}-gtk4-demo-title-app-title-half.png
${BUILDER-BUTTON}           ${T}/${SCALE}-gtk4-demo-button-builder.png
${BUILDER-TITLE}            ${T}/${SCALE}-gtk4-demo-title-builder.png
>>>>>>> b06e541 (scale: add half-aligned title template)


*** Test Cases ***
Ensure Scaling Is Visually Correct
    Move Pointer To Proportional (1.0, 1.0)
    Match                   ${T}/${SCALE}-gtk4-demo-screenshot-floating.png

<<<<<<< HEAD
    Walk Pointer To ${T}/${SCALE}-gtk4-demo-title-app-title.png
=======
    ${aligned}=             Run Keyword And Return Status
    ...                     Walk Pointer To ${DEMO-APP-TITLE}
    IF    ${aligned} == False    Walk Pointer To ${DEMO-APP-TITLE-HALF}
>>>>>>> b06e541 (scale: add half-aligned title template)
    Click LEFT Button
    Click LEFT Button
    Move Pointer To Proportional (1.0, 1.0)

    Match                   ${T}/${SCALE}-gtk4-demo-screenshot-maximized.png

    Walk Pointer To ${T}/${SCALE}-gtk4-demo-title-app-title.png
    Click LEFT Button
    Click LEFT Button

Click Button With Fractional Scaling Enabled
    Move Pointer To Proportional (1.0, 1.0)
<<<<<<< HEAD
    Walk Pointer To ${T}/${SCALE}-gtk4-demo-title-app-title.png
=======
    ${aligned}=             Run Keyword And Return Status
    ...                     Walk Pointer To ${DEMO-APP-TITLE}
    IF    ${aligned} == False    Walk Pointer To ${DEMO-APP-TITLE-HALF}
>>>>>>> b06e541 (scale: add half-aligned title template)
    Click LEFT Button
    Click LEFT Button

    Move Pointer To ${COMBO-BOXES}
    Click LEFT Button

    Match                   ${T}/${SCALE}-gtk4-demo-title-combo-boxes-maximized.png
