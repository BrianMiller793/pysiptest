Feature: Renewals for SUBSCRIBE request

  Scenario: Alice registers and subscribes
    Given "Alice" registers
    Then pause for 1 seconds
    Then "Alice" subscribes to "Bob"
    Then pause for 1 seconds
    Then "Alice" unsubscribes from "Bob"
    Then pause for 1 seconds

  Scenario: Alice registers, subscribes and renews
    Given "Alice" registers
    Then "Alice" subscribes to "Bob"
    Then pause for 1 seconds
    # Actually a renewal with fresh credentials
    Then "Alice" subscribes to "Bob"
    Then pause for 1 seconds
    Then "Alice" unsubscribes from "Bob"
    Then pause for 1 seconds

  Scenario: Alice registers, subscribes and renews with cached auth
    Given "Alice" registers
    Then "Alice" subscribes to "Bob"
    Then pause for 1 seconds
    Then "Alice" renews subscription with cached authentication to "Bob" and expect "202"
    Then pause for 1 seconds
    Then "Alice" unsubscribes from "Bob"
    Then pause for 1 seconds

  # This external address is from: stun stun.freeswitch.org -v
  Scenario: Subscription uses STUN external address
    Given "Alice" registers
    Then "Alice" subscribes to "Bob"
    Then pause for 1 seconds
    Then "Alice" sets "sip_auth_uri" to "sip:2000@50.34.59.190:5060"
    Then "Alice" renews subscription with cached authentication to "sip:2001@50.34.59.190:5060" and expect "202"
    Then pause for 1 seconds
    Then "Alice" unsubscribes from "Bob"
    Then pause for 1 seconds

  Scenario: Subscription uses local NAT address
    Given "Alice" registers
    Then "Alice" subscribes to "Bob"
    Then pause for 1 seconds
    Then "Alice" sets "sip_auth_uri" to "sip:2000@192.168.0.143:5060"
    Then "Alice" renews subscription with cached authentication to "sip:2001@192.168.0.143:5060" and expect "202"
    Then pause for 1 seconds
    Then "Alice" unsubscribes from "Bob"
    Then pause for 1 seconds

  Scenario: Renewal is outside sofia default 60 second nonce-ttl value
    Given "Alice" registers
    Then "Alice" subscribes to "Bob"
    Then pause for 90 seconds
    Then "Alice" renews subscription with cached authentication to "Bob" and expect "401"
    Then pause for 1 seconds
    Then "Alice" unsubscribes from "Bob"
    Then pause for 1 seconds
