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

Drag And Drop Both To Text
    Walk Pointer To ${SRC_BOTH}
    Click LEFT Button
    Walk Pointer To ${DST_TEXT}
    Click LEFT Button

    Walk Pointer To ${ITEM}
    Press LEFT Button
    Walk Pointer To ${TARGET}
    Release Buttons
    Match                   ${T}/dnd_nothing.png

Drag And Drop Text To Text
    Walk Pointer To ${SRC_TEXT}
    Click LEFT Button
    Walk Pointer To ${DST_TEXT}
    Click LEFT Button

    Walk Pointer To ${ITEM}
    Press LEFT Button
    Walk Pointer To ${TARGET}
    Match                   ${T}/dnd_action_copy.png
    Release Buttons
    Match                   ${T}/dnd_received_text.png

Drag And Drop Image To Image
    Walk Pointer To ${SRC_IMAGES}
    Click LEFT Button
    Walk Pointer To ${DST_IMAGES}
    Click LEFT Button

    Walk Pointer To ${ITEM}
    Press LEFT Button
    Walk Pointer To ${TARGET}
    Match                   ${T}/dnd_action_copy.png
    Release Buttons
    Match                   ${T}/dnd_received_pixbuf.png

Drag And Drop Text To Image
    Walk Pointer To ${SRC_TEXT}
    Click LEFT Button
    Walk Pointer To ${DST_IMAGES}
    Click LEFT Button

    Walk Pointer To ${ITEM}
    Press LEFT Button
    Walk Pointer To ${TARGET}
    Match                   ${T}/dnd_action_copy.png
    Release Buttons
    Match                   ${T}/dnd_received_pixbuf.png

Drag And Drop Both To Image
    Walk Pointer To ${SRC_BOTH}
    Click LEFT Button
    Walk Pointer To ${DST_IMAGES}
    Click LEFT Button

    Walk Pointer To ${ITEM}
    Press LEFT Button
    Walk Pointer To ${TARGET}
    Match                   ${T}/dnd_action_copy.png
    Release Buttons
    Match                   ${T}/dnd_received_pixbuf.png


*** Keywords ***
Suite Setup
    Move Pointer To Proportional (0.5, 0.5)
    ${src_both}=            Move Pointer To ${T}/dnd_setup.png
    ${src_images}=          Displace ${src_both} By (-137, 0)
    ${src_text}=            Displace ${src_both} By (-64, 0)
    ${dst_images}=          Displace ${src_both} By (85, 0)
    ${dst_text}=            Displace ${src_both} By (156, 0)
    Set Suite Variable      ${SRC_IMAGES}           ${src_images}
    Set Suite Variable      ${SRC_TEXT}             ${src_text}
    Set Suite Variable      ${SRC_BOTH}             ${src_both}
    Set Suite Variable      ${DST_IMAGES}           ${dst_images}
    Set Suite Variable      ${DST_TEXT}             ${dst_text}

    ${item}=                Move Pointer To ${T}/dnd_sources.png
    Set Suite Variable      ${ITEM}                 ${item}

    ${target}=              Move Pointer To ${T}/dnd_target.png
    Set Suite Variable      ${TARGET}               ${target}
