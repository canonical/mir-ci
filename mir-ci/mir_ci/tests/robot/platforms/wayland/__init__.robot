*** Settings ***
Documentation       Wayland resources

Suite Setup         Setup Suite


*** Keywords ***
Setup Suite
    Set Global Variable     ${KVM_RESOURCE}         ${CURDIR}/WaylandKVM.resource
