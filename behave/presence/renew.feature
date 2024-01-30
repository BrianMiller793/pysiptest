Feature: Renewals for SUBSCRIBE request

  Scenario: Alice registers, subscribes, and renews
    Given "Alice" registers
    Then pause for 1 seconds
    Then "Alice" subscribes to "Bob"
    Then pause for 1 seconds
    # This is actually a renewal
    Then "Alice" subscribes to "Bob"
    Then pause for 1 seconds
    Then "Alice" unsubscribes from "Bob"
    Then fail
