Feature: Presence Notification Represents Call and User States

  Scenario: Activity Creates Presence Notification
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

  Scenario: User-initiated Presence Settings are Reflected by UC
    Given "Alice" registers
    Then pause for 1 seconds
    Given "Bob" registers
    Then pause for 1 seconds
    Then "Bob" subscribes to "Alice"
    Then pause for 1 seconds

    Then "Alice" sets presence to "After Hours"
    Then pause for 1 seconds
    Then "Bob" has received "After Hours" notification for "Alice"

    Then "Alice" sets presence to "Away"
    Then pause for 1 seconds
    Then "Bob" has received "Away" notification for "Alice"

    #Then "Alice" sets presence to "Call Forward 2001"
    #Then pause for 1 seconds
    #Then "Bob" has received "" notification for "Alice"

    Then "Alice" sets presence to "Busy"
    Then pause for 1 seconds
    Then "Bob" has received "Busy" notification for "Alice"

    Then "Alice" sets presence to "Do Not Disturb"
    Then pause for 1 seconds
    Then "Bob" has received "Do Not Disturb" notification for "Alice"

    Then "Alice" sets presence to "Not Available"
    Then pause for 1 seconds
    Then "Bob" has received "Not Available" notification for "Alice"

    Then "Alice" sets presence to "On Holiday"
    Then pause for 1 seconds
    Then "Bob" has received "On Holiday" notification for "Alice"

    Then "Alice" sets presence to "On Vacation"
    Then pause for 1 seconds
    Then "Bob" has received "On Vacation" notification for "Alice"

    Then "Alice" sets presence to "Available"
    Then pause for 1 seconds
    Then "Bob" has received "Available" notification for "Alice"

    Then "Bob" unsubscribes from "Alice"
    Then "Alice" unregisters
    Then "Bob" unregisters
