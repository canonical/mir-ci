*** Settings ***
Resource        ${KVM_RESOURCE}

Test Setup      Set Output Scale    ${SCALE}


*** Variables ***
${T}                ${CURDIR}
${COMBO-BOXES}      ${T}/${SCALE}-gtk4-demo-button-combo-boxes-maximized.png


*** Test Cases ***
Ensure Scaling Is Visually Correct
    Move Pointer To Proportional (1.0, 1.0)
    Match                   ${T}/${SCALE}-gtk4-demo-screenshot-floating.png

    Walk Pointer To ${T}/${SCALE}-gtk4-demo-title-app-title.png
    Click LEFT Button
    Click LEFT Button
    Move Pointer To Proportional (1.0, 1.0)

    Match                   ${T}/${SCALE}-gtk4-demo-screenshot-maximized.png

    Walk Pointer To ${T}/${SCALE}-gtk4-demo-title-app-title.png
    Click LEFT Button
    Click LEFT Button

Click Button With Fractional Scaling Enabled
    Move Pointer To Proportional (1.0, 1.0)
    Walk Pointer To ${T}/${SCALE}-gtk4-demo-title-app-title.png
    Click LEFT Button
    Click LEFT Button

    ${match_found}=         Run Keyword and Return Status
    ...                     Match                   ${COMBO-boxes}

    IF    ${match_found} == ${FALSE}
        Move Pointer To Proportional (0.1, 0.5)
        Scroll Until Match ${COMBO-boxes}
    END

    Move Pointer To ${COMBO-boxes}
    Click LEFT Button

    Match                   ${T}/${SCALE}-gtk4-demo-title-combo-boxes-maximized.png
