Feature: Test SIP CANCEL behavior

  Scenario: Alice calls Bob, Bob answers
    Given Alice registers
    Given Bob registers
    Then pause for 1 seconds
    Then Bob expects a call
    Then Alice calls Bob
    Then Bob answers the call
    Then pause for 10 seconds
    Then Bob hangs up

  Scenario: Alice calls Bob, Bob doesn't answer
    Given Alice registers
    Given Bob registers
    Then pause for 1 seconds
    Then Bob lets phone ring 30 times before answering
    Then Alice rings Bob for 5 seconds
    Then Alice cancels the call
    Then Bob has missed a call
