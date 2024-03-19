*** Settings ***
Resource    ${KVM_RESOURCE}
Resource    ${CURDIR}/osk.resource


*** Variables ***
${T}    ${CURDIR}


*** Test Cases ***
Type into Pluma
    Move Pointer To (0, 0)
    Match                   ${T}/01_pluma.png

    Press OSK shift
    Match OSK upper
    Type                    This is
    Press OSK space
    Press OSK shift
    Type                    Frame
    Press OSK 123
    Press OSK !
    Press OSK enter
    Press OSK enter
    Press OSK ABC
    Press OSK shift
    Press OSK shift
    Type                    ALL CAPS
    Press OSK enter
    Press OSK enter
    Type                    A
    Press OSK shift
    Type                    nd
    Press OSK space
    Switch OSK To emoji
    Type                    😎
    Switch OSK To default
    Press OSK space
    Press OSK shift
    Type                    Emoji
    Match                   ${T}/02_this_is_frame.png
