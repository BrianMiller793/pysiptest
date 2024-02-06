Feature: Alice Makes Calls

  Scenario: Alice calls Bob
    Given "Alice" registers
    Given "Bob" registers
    Then pause for 1 seconds
    Then "Bob" waits for a call
    Then "Alice" calls "Bob"
    Then "Bob" answers the call
    Then pause for 5 seconds
    Then "Bob" hangs up
