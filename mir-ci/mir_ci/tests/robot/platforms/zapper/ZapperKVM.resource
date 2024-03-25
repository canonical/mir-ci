*** Settings ***
Library     libraries/VideoInput.py    ${VIDEO_SOURCE}    AS    VIDEO
Library     ${CURDIR}/ZapperHid.py    AS    HID
Resource    ${CURDIR}/kvm.resource
