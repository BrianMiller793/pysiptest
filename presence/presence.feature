Feature: Park Calls

  @wip
  Scenario: Park on mod_valet_parking with Three Endpoints
    Given "Alice" registers
    Then pause for 1 seconds
    Given "Bob" registers
    Then pause for 1 seconds
    Given "Charlie" registers
    Then pause for 1 seconds

    Then "Charlie" subscribes to "Alice"
    Then "Charlie" subscribes to "Bob"
    Then pause for 2 seconds
    Then "Charlie" has received "Available" notification for "Alice"
    Then "Charlie" has received "Available" notification for "Bob"

    Then "Bob" waits for a call
    Then "Alice" calls "Bob"
    Then "Bob" answers the call
    Then pause for 2 seconds
    Then "Charlie" has received "On The Phone" notification for "Alice"
    Then "Charlie" has received "On The Phone" notification for "Bob"
    Then "Bob" hangs up
    Then pause for 2 seconds
    Then "Charlie" has received "Available" notification for "Alice"
    Then "Charlie" has received "Available" notification for "Bob"

    Then "Charlie" unsubscribes from "Alice"
    Then "Charlie" unsubscribes from "Bob"

    Then "Alice" unregisters
    Then "Bob" unregisters
    Then "Charlie" unregisters
