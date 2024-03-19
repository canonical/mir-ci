*** Settings ***
Resource    ${KVM_RESOURCE}
Library     ${CURDIR}/OSKMap.py


*** Variables ***
${OSK_LAYOUT}=      default
${OSK_REGION}=      None
${OSK_T}=           ${CURDIR}/osk_


*** Keywords ***
Initialize OSK
    IF    ${OSK_REGION} == None
        Move Pointer To (0, 0)
        ${ret}=                 Match                   ${OSK_T}${OSK_LAYOUT}.png
        Set Suite Variable      ${OSK_REGION}           ${ret}[0]
        Move Pointer To (${OSK_REGION}[left], ${OSK_REGION}[top])
    END

Match OSK ${template}
    Initialize OSK
    ${pos}=                 Match                   ${OSK_T}${template}.png
    RETURN                  ${pos}[0]

Press OSK ${key}
    Initialize OSK
    ${pos}=                 Get Point For Key       ${OSK_LAYOUT}           ${OSK_REGION}           ${key}
    Walk Pointer To ${pos}
    Click LEFT Button

Switch OSK To ${layout}
    Press OSK layouts
    Walk Pointer To ${OSK_T}layout_${layout}.png
    Click LEFT Button
    ${ret}=                 Match OSK ${layout}
    Move Pointer To (${ret}[left], ${ret}[top])

    Set Suite Variable      ${OSK_REGION}           ${ret}
    Set Suite Variable      ${OSK_LAYOUT}           ${layout}

Type
    [Arguments]             ${text}
    ${text}=                Evaluate                list('${text}')
    ${last_char}=           Evaluate                ''
    FOR    ${char}    IN    @{text}
        IF    '${char}' == '${last_char}'
            Click LEFT Button
        ELSE IF    '${char}' == ' '
            Press OSK space
        ELSE
            Press OSK ${char}
        END
        ${last_char}=           Evaluate                '${char}'
    END
