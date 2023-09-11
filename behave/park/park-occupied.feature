Feature: Park Calls

  Scenario: Register and Unregister
    Given "Alice" registers
    Given "Bob" registers
    Given "Charlie" registers

    And "Charlie" waits for a call

    Then "Alice" calls "Charlie"
    Then "Charlie" answers the call
    Then pause for 2 seconds
    Then "Charlie" parks "Alice" on "sip:park+500@teo"
    Then "Charlie" waits for a call

    Then pause for 2 seconds

    Then "Bob" calls "Charlie"
    Then "Charlie" answers the call
    Then pause for 2 seconds
    Then "Charlie" parks "Bob" on "sip:park+500@teo"
    And "Charlie" waits for a call

    Then "Charlie" answers the call
    Then "Bob" starts waiting
    Then pause for 2 seconds

    Then "Charlie" hangs up

    Then "Bob" waits for hangup

    Then "Alice" hangs up

    Then "Alice" unregisters
    Then "Bob" unregisters
    Then "Charlie" unregisters

