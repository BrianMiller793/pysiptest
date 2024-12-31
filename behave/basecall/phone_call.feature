Feature: Dave Makes Calls

  Scenario: Dave calls Charlie
    Given Dave registers
    Given Charlie registers
    Then pause for 1 seconds

    Then Charlie expects a call
    Then Dave calls Charlie
    Then Charlie answers the call
    Then pause for 300 seconds between Dave and Charlie
    Then Charlie hangs up
    Then pause for 1 seconds
