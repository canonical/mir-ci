*** Settings ***
Documentation       Wayland resources

Suite Setup         Setup Suite


*** Variables ***
${KVM_RESOURCE}     ${CURDIR}${/}KVM.resource


*** Keywords ***
Setup Suite
    Set Global Variable     ${KVM_RESOURCE}         ${KVM_RESOURCE}
