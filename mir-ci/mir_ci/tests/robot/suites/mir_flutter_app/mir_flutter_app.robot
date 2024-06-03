*** Settings ***
Resource    ${KVM_RESOURCE}


*** Variables ***
${T}                                        ${CURDIR}

${ANCHOR_OPTION_TOP_LEFT}                   ${T}/anchor_option_top_left.png
${ANCHOR_OPTION_BOTTOM_RIGHT}               ${T}/anchor_option_bottom_right.png

${BUTTON_CLOSE_FOCUSED}                     ${T}/button_close_focused.png

${DIALOG_CUSTOM_POSITIONER}                 ${T}/dialog_custom_positioner.png

${EXPECTED_SATELLITE_PLACEMENT}             ${T}/expected_satellite_placement.png
${EXPECTED_WINDOW_BEFORE_MOVE}              ${T}/expected_window_before_move.png
${EXPECTED_WINDOW_AFTER_MOVE}               ${T}/expected_window_after_move.png
${EXPECTED_POPUP_PLACEMENT_SLIDE}           ${T}/expected_popup_placement_slide.png
${EXPECTED_POPUP_PLACEMENT_FLIP}            ${T}/expected_popup_placement_flip.png
${EXPECTED_POPUP_PLACEMENT_RESIZE}          ${T}/expected_popup_placement_resize.png

${GROUP_NEW_WINDOW}                         ${T}/group_new_window.png

${WINDOW_MAIN}                              ${T}/window_main.png
${WINDOW_REGULAR_0_FOCUSED}                 ${T}/window_regular_0_focused.png
${WINDOW_FLOATING_REGULAR_0_FOCUSED}        ${T}/window_floating_regular_0_focused.png
${WINDOW_FLOATING_REGULAR_0_NON_FOCUSED}    ${T}/window_floating_regular_0_non_focused.png
${WINDOW_DIALOG_FOCUSED}                    ${T}/window_dialog_focused.png
${WINDOW_SATELLITE_1}                       ${T}/window_satellite_1.png
${WINDOW_POPUP_1}                           ${T}/window_popup_1.png
${WINDOW_TIP_1}                             ${T}/window_tip_1.png


*** Test Cases ***
Reference App Opens
    VIDEO.Match             ${WINDOW_MAIN}

Regular Window Opens
    Open REGULAR Window
    VIDEO.Match             ${WINDOW_REGULAR_0_FOCUSED}
    Close Focused Toplevel Window

Floating Regular Window Opens
    Open FLOATING_REGULAR Window
    VIDEO.Match             ${WINDOW_FLOATING_REGULAR_0_FOCUSED}
    Close Focused Toplevel Window

Dialog Window Opens
    Open DIALOG Window
    VIDEO.Match             ${WINDOW_DIALOG_FOCUSED}
    Close Focused Toplevel Window

Satellite Window Opens
    Open REGULAR Window
    Open SATELLITE Window
    Walk Pointer To ${WINDOW_SATELLITE_1}
    Click LEFT Button
    Close Focused Toplevel Window

Popup Window Opens
    Open REGULAR Window
    Open POPUP Window
    Walk Pointer To ${WINDOW_POPUP_1}
    Click LEFT Button
    Close Focused Toplevel Window

Tip Window Opens
    Open REGULAR Window
    Open TIP Window
    Walk Pointer To ${WINDOW_TIP_1}
    Click LEFT Button
    Close Focused Toplevel Window

Floating Regular Window Stays On Top
    Open FLOATING_REGULAR Window
    Walk Pointer To ${GROUP_NEW_WINDOW}
    Click LEFT Button
    Walk Pointer To ${WINDOW_FLOATING_REGULAR_0_NON_FOCUSED}
    Click LEFT Button
    Close Focused Toplevel Window

Dialog Is Modal To Parent
    Open REGULAR Window
    Open DIALOG Window
    # Try to close parent
    ${pos}=                 Walk Pointer To ${WINDOW_REGULAR_0_FOCUSED}
    ${pos}=                 Displace ${pos} By (130, 0)
    Walk Pointer To ${pos}
    Click LEFT Button
    # Expect parent to be still open
    VIDEO.Match             ${WINDOW_REGULAR_0_FOCUSED}
    Close Dialog Window
    Close Focused Toplevel Window

Satellite Is Placed According To Custom Positioner
    Select CUSTOM Positioner Preset
    Open FLOATING_REGULAR Window
    Open SATELLITE Window
    VIDEO.Match             ${EXPECTED_SATELLITE_PLACEMENT}
    Close Focused Toplevel Window

Child Windows Move With Parent
    Open FLOATING_REGULAR Window
    Select LEFT Positioner Preset
    Open SATELLITE Window
    Select BOTTOM_LEFT Positioner Preset
    Open POPUP Window
    Select BOTTOM Positioner Preset
    Open TIP Window
    Select CENTER Positioner Preset
    Open DIALOG Window
    ${pos}=                 Walk Pointer To ${WINDOW_FLOATING_REGULAR_0_FOCUSED}
    Press LEFT Button
    VIDEO.Match             ${EXPECTED_WINDOW_BEFORE_MOVE}
    ${pos}=                 Displace ${pos} By (50, 25)
    Walk Pointer To ${pos}
    Release LEFT Button
    VIDEO.Match             ${EXPECTED_WINDOW_AFTER_MOVE}
    Close Dialog Window
    Close Focused Toplevel Window

Slide Constraint Is Applied
    Set Top Left Custom Positioner
    Move Main Window To The Top Left Of The Output
    Open FLOATING_REGULAR Window
    Walk Pointer To ${WINDOW_FLOATING_REGULAR_0_FOCUSED}
    Press LEFT Button
    Walk Pointer To (250, 90)
    Release LEFT Button
    Open POPUP Window
    VIDEO.Match             ${EXPECTED_POPUP_PLACEMENT_SLIDE}
    Close Focused Toplevel Window

Flip Constraint Is Applied
    Set Top Left Custom Positioner
    Open Custom Positioner Dialog
    ${pos}=                 Walk Pointer To ${DIALOG_CUSTOM_POSITIONER}
    # Uncheck 'slide X' checkbox
    ${pos}=                 Displace ${pos} By (-5, 370)
    Walk Pointer To ${pos}
    Click LEFT Button
    # Uncheck 'slide Y' checkbox
    ${pos}=                 Walk Pointer To ${DIALOG_CUSTOM_POSITIONER}
    ${pos}=                 Displace ${pos} By (70, 370)
    Walk Pointer To ${pos}
    Click LEFT Button
    # Check 'flip X' checkbox
    ${pos}=                 Walk Pointer To ${DIALOG_CUSTOM_POSITIONER}
    ${pos}=                 Displace ${pos} By (-5, 400)
    Walk Pointer To ${pos}
    Click LEFT Button
    # Check 'flip Y' checkbox
    ${pos}=                 Walk Pointer To ${DIALOG_CUSTOM_POSITIONER}
    ${pos}=                 Displace ${pos} By (70, 400)
    Walk Pointer To ${pos}
    Click LEFT Button
    # Walk Pointer To ${BUTTON_APPLY}
    # Click LEFT Button
    Press Apply Button
    Move Main Window To The Top Left Of The Output
    Open FLOATING_REGULAR Window
    Walk Pointer To ${WINDOW_FLOATING_REGULAR_0_FOCUSED}
    Press LEFT Button
    Walk Pointer To (250, 90)
    Release LEFT Button
    Open POPUP Window
    VIDEO.Match             ${EXPECTED_POPUP_PLACEMENT_FLIP}
    Close Focused Toplevel Window

Resize Constraint Is Applied
    Set Top Left Custom Positioner
    Open Custom Positioner Dialog
    ${pos}=                 Walk Pointer To ${DIALOG_CUSTOM_POSITIONER}
    # Uncheck 'slide X' checkbox
    ${pos}=                 Displace ${pos} By (-5, 370)
    Walk Pointer To ${pos}
    Click LEFT Button
    # Uncheck 'slide Y' checkbox
    ${pos}=                 Walk Pointer To ${DIALOG_CUSTOM_POSITIONER}
    ${pos}=                 Displace ${pos} By (70, 370)
    Walk Pointer To ${pos}
    Click LEFT Button
    # Check 'resize X' checkbox
    ${pos}=                 Walk Pointer To ${DIALOG_CUSTOM_POSITIONER}
    ${pos}=                 Displace ${pos} By (-5, 430)
    Walk Pointer To ${pos}
    Click LEFT Button
    # Check 'resize Y' checkbox
    ${pos}=                 Walk Pointer To ${DIALOG_CUSTOM_POSITIONER}
    ${pos}=                 Displace ${pos} By (70, 430)
    Walk Pointer To ${pos}
    Click LEFT Button
    # Walk Pointer To ${BUTTON_APPLY}
    # Click LEFT Button
    Press Apply Button
    Move Main Window To The Top Left Of The Output
    Open FLOATING_REGULAR Window
    Walk Pointer To ${WINDOW_FLOATING_REGULAR_0_FOCUSED}
    Press LEFT Button
    Walk Pointer To (250, 60)
    Release LEFT Button
    Open POPUP Window
    VIDEO.Match             ${EXPECTED_POPUP_PLACEMENT_RESIZE}
    Close Focused Toplevel Window

Flip Constraint Precedes Slide
    Set Top Left Custom Positioner
    Open Custom Positioner Dialog
    # Check 'flip X' checkbox
    ${pos}=                 Walk Pointer To ${DIALOG_CUSTOM_POSITIONER}
    ${pos}=                 Displace ${pos} By (-5, 400)
    Walk Pointer To ${pos}
    Click LEFT Button
    # Check 'flip Y' checkbox
    ${pos}=                 Walk Pointer To ${DIALOG_CUSTOM_POSITIONER}
    ${pos}=                 Displace ${pos} By (70, 400)
    Walk Pointer To ${pos}
    Click LEFT Button
    # Walk Pointer To ${BUTTON_APPLY}
    # Click LEFT Button
    Press Apply Button
    Move Main Window To The Top Left Of The Output
    Open FLOATING_REGULAR Window
    Walk Pointer To ${WINDOW_FLOATING_REGULAR_0_FOCUSED}
    Press LEFT Button
    Walk Pointer To (250, 90)
    Release LEFT Button
    Open POPUP Window
    VIDEO.Match             ${EXPECTED_POPUP_PLACEMENT_FLIP}
    Close Focused Toplevel Window

Slide Constraint Precedes Resize
    Set Top Left Custom Positioner
    Open Custom Positioner Dialog
    # Check 'resize X' checkbox
    ${pos}=                 Walk Pointer To ${DIALOG_CUSTOM_POSITIONER}
    ${pos}=                 Displace ${pos} By (-5, 430)
    Walk Pointer To ${pos}
    Click LEFT Button
    # Check 'resize Y' checkbox
    ${pos}=                 Walk Pointer To ${DIALOG_CUSTOM_POSITIONER}
    ${pos}=                 Displace ${pos} By (70, 430)
    Walk Pointer To ${pos}
    Click LEFT Button
    # Walk Pointer To ${BUTTON_APPLY}
    # Click LEFT Button
    Press Apply Button
    Move Main Window To The Top Left Of The Output
    Open FLOATING_REGULAR Window
    Walk Pointer To ${WINDOW_FLOATING_REGULAR_0_FOCUSED}
    Press LEFT Button
    Walk Pointer To (250, 90)
    Release LEFT Button
    Open POPUP Window
    VIDEO.Match             ${EXPECTED_POPUP_PLACEMENT_SLIDE}
    Close Focused Toplevel Window


*** Keywords ***
Close Focused Toplevel Window
    Walk Pointer To ${BUTTON_CLOSE_FOCUSED}
    Click LEFT Button

Close Dialog Window
    ${pos}=                 Walk Pointer To ${WINDOW_DIALOG_FOCUSED}
    ${pos}=                 Displace ${pos} By (112, 0)
    Walk Pointer To ${pos}
    Click LEFT Button

Select ${preset} Positioner Preset
    ${vertical_distance_between_options}=           Set Variable            48

    # Reset first to make sure the dropdown list is positioned as expected
    ${pos}=                 Move Pointer To ${GROUP_NEW_WINDOW}
    ${pos}=                 Displace ${pos} By (0, 390)
    Walk Pointer To ${pos}
    Click LEFT Button
    ${pos}=                 Displace ${pos} By (0, -${vertical_distance_between_options})
    Walk Pointer To ${pos}
    # Wait for the dropdown list to show up
    Sleep                   1
    Click LEFT Button

    # Select preset
    ${pos}=                 Move Pointer To ${GROUP_NEW_WINDOW}
    ${pos}=                 Displace ${pos} By (0, 390)
    Walk Pointer To ${pos}
    Click LEFT Button
    IF    $preset == "LEFT"
        ${pos}=                 Displace ${pos} By (0, ${vertical_distance_between_options} * -5)
    ELSE IF    $preset == "RIGHT"
        ${pos}=                 Displace ${pos} By (0, ${vertical_distance_between_options} * -4)
    ELSE IF    $preset == "BOTTOM_LEFT"
        ${pos}=                 Displace ${pos} By (0, ${vertical_distance_between_options} * -3)
    ELSE IF    $preset == "BOTTOM"
        ${pos}=                 Displace ${pos} By (0, ${vertical_distance_between_options} * -2)
    ELSE IF    $preset == "BOTTOM_RIGHT"
        ${pos}=                 Displace ${pos} By (0, ${vertical_distance_between_options} * -1)
    ELSE IF    $preset == "CENTER"
        ${pos}=                 Displace ${pos} By (0, ${vertical_distance_between_options} * 0)
    ELSE IF    $preset == "CUSTOM"
        ${pos}=                 Displace ${pos} By (0, ${vertical_distance_between_options} * 1)
    ELSE
        Fail                    Unexpected preset: ${preset}
    END
    # Wait for the dropdown list to show up
    Sleep                   1
    Walk Pointer To ${pos}
    Click LEFT Button

Move Main Window To The Top Left Of The Output
    ${pos}=                 Move Pointer To ${GROUP_NEW_WINDOW}
    ${pos}=                 Displace ${pos} By (0, -77)
    Walk Pointer To ${pos}
    Press LEFT Button
    Walk Pointer To (600, 0)
    Release LEFT Button

Open ${window} Window
    ${vertical_distance_between_options}=           Set Variable            40
    ${pos}=                 Move Pointer To ${GROUP_NEW_WINDOW}
    IF    $window == "REGULAR"
        ${pos}=                 Displace ${pos} By (0, ${vertical_distance_between_options} * 1)
    ELSE IF    $window == "FLOATING_REGULAR"
        ${pos}=                 Displace ${pos} By (0, ${vertical_distance_between_options} * 2)
    ELSE IF    $window == "DIALOG"
        ${pos}=                 Displace ${pos} By (0, ${vertical_distance_between_options} * 3)
    ELSE IF    $window == "SATELLITE"
        ${pos}=                 Displace ${pos} By (0, ${vertical_distance_between_options} * 4)
    ELSE IF    $window == "POPUP"
        ${pos}=                 Displace ${pos} By (0, ${vertical_distance_between_options} * 5)
    ELSE IF    $window == "TIP"
        ${pos}=                 Displace ${pos} By (0, ${vertical_distance_between_options} * 6)
    ELSE
        Fail                    Unexpected window: ${window}
    END
    Move Pointer To ${pos}
    Click LEFT Button

Open Custom Positioner Dialog
    ${pos}=                 Move Pointer To ${GROUP_NEW_WINDOW}
    ${pos}=                 Displace ${pos} By (0, 450)
    Move Pointer To ${pos}
    Click LEFT Button

Open Parent Anchor Dropdown List
    ${pos}=                 Move Pointer To ${DIALOG_CUSTOM_POSITIONER}
    ${pos}=                 Displace ${pos} By (0, 75)
    Move Pointer To ${pos}
    Click LEFT Button

Open Child Anchor Dropdown List
    ${pos}=                 Move Pointer To ${DIALOG_CUSTOM_POSITIONER}
    ${pos}=                 Displace ${pos} By (0, 170)
    Move Pointer To ${pos}
    Click LEFT Button

Press Set Defaults Button
    ${pos}=                 Move Pointer To ${DIALOG_CUSTOM_POSITIONER}
    ${pos}=                 Displace ${pos} By (-55, 470)
    Move Pointer To ${pos}
    Click LEFT Button

Press Apply Button
    ${pos}=                 Move Pointer To ${DIALOG_CUSTOM_POSITIONER}
    ${pos}=                 Displace ${pos} By (60, 470)
    Move Pointer To ${pos}
    Click LEFT Button

Set Top Left Custom Positioner
    Open Custom Positioner Dialog
    Press Set Defaults Button
    Open Parent Anchor Dropdown List
    Walk Pointer To ${ANCHOR_OPTION_TOP_LEFT}
    Click LEFT Button
    Open Child Anchor Dropdown List
    Walk Pointer To ${ANCHOR_OPTION_BOTTOM_RIGHT}
    Click LEFT Button
    Press Apply Button
