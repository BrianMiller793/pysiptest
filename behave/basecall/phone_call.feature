Feature: Dave Makes Calls

  Scenario: Dave calls Charlie
    Given Dave registers
    Given Charlie registers
    Then pause for 1 seconds

    Then Charlie expects a call
    Then Dave calls Charlie
    Then Charlie answers the call
    Then pause for 10 seconds
    Then Charlie hangs up
    Then pause for 5 seconds

    Then Charlie expects a call
    Then Dave calls Charlie
    Then Charlie answers the call
    Then pause for 65 seconds
    Then Dave hangs up
    Then pause for 5 seconds

    Then Charlie expects a call
    Then Dave calls Charlie
    Then Charlie answers the call
    Then pause for 15 seconds
    Then Dave registers
    Then Charlie registers
    Then pause for 100 seconds
    Then Charlie hangs up
    Then pause for 1 seconds
