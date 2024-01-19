*** Settings ***
Documentation     Robot test suite for mir-ci

Resource          ../resources/drag_and_drop.resource

# Suite Setup       Log    Performing suite setup steps
# Suite Teardown    Log    Performing suite teardown steps
# Test Setup        Log    Performing test setup steps
# Test Teardown     Log    Performing test teardown steps

*** Test Cases ***
Drag And Drop Match
    [Documentation]    Tests matches
    Test Source And Destination Match

Drag And Drop Mismatch
    [Documentation]    Tests mismatches
    Test Source And Destination Mismatch
