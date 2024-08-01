Feature: Alice Makes Calls

  Scenario: Alice calls Bob
    Given "Alice1" registers
    Given "Bob1" registers
    Then pause for 1 seconds
    Then "Bob1" expects a call
    Then "Alice1" calls "Bob1"
    Then "Bob1" answers the call
    Then pause for 30 seconds
    Then "Bob1" hangs up
    Then pause for 1 seconds
    Then "Alice1" unregisters
    Then "Bob1" unregisters
    Then pause for 1 seconds
