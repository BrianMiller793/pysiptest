Feature: Park Calls

  Scenario: Park on mod_valet_parking with Three Endpoints
    Given "Alice" registers
    Given "Bob" registers
    Given "Charlie" registers

    And "Bob" waits for a call
    Then "Alice" calls "Bob"
    Then "Bob" answers the call
    Then pause for 2 seconds
    Then "Bob" parks "Alice" on "sip:park+500@teo"
    Then pause for 2 seconds

    Then "Charlie" unparks "Alice" from "sip:park+500@teo"
    Then "Alice" starts waiting
    Then pause for 2 seconds
    Then "Charlie" hangs up
    Then "Alice" waits for hangup

    Then "Alice" unregisters
    Then "Bob" unregisters
    Then "Charlie" unregisters

  Scenario: Park on legacy park with Three Endpoints
    Given "Alice" registers
    Given "Bob" registers
    Given "Charlie" registers

    And "Bob" waits for a call
    Then "Alice" calls "Bob"
    Then "Bob" answers the call
    Then pause for 2 seconds
    Then "Bob" parks "Alice" on "sip:*712008@teo"
    Then pause for 2 seconds

    Then "Charlie" unparks "Alice" from "sip:*722008@teo"
    Then "Alice" starts waiting
    Then pause for 2 seconds
    Then "Charlie" hangs up
    Then "Alice" waits for hangup

    Then "Alice" unregisters
    Then "Bob" unregisters
    Then "Charlie" unregisters
