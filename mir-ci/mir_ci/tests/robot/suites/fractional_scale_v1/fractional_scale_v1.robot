*** Settings ***
Resource        ${KVM_RESOURCE}

Suite Setup     Suite Setup


*** Variables ***
${T}    ${CURDIR}


*** Test Cases ***
Drag And Drop Image To Text
    Walk Pointer To ${SRC_IMAGES}
    Click LEFT Button
    Walk Pointer To ${DST_TEXT}
    Click LEFT Button

    Walk Pointer To ${ITEM}
    Press LEFT Button
    Walk Pointer To ${TARGET}
    Release Buttons
    Match                   ${T}/dnd_nothing.png

