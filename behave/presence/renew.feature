Feature: Renewals for SUBSCRIBE request

  Scenario: Alice registers, subscribes, and renews
    Given "Alice" registers
    Then pause for 1 seconds
    Then "Alice" subscribes to "Bob"
    Then pause for 1 seconds
    # Now test the renewals
    Then "Alice" renews subscription with authentication to "Bob"
    Then pause for 1 seconds
    # This external address is from: stun stun.freeswitch.org -v
    Then "Alice" sets "sip_auth_uri" to "sip:2000@50.34.42.8:5060"
    Then "Alice" renews subscription with authentication to "Bob"
    Then pause for 1 seconds
    # This address is the FreeSWITCH UC
    Then "Alice" sets "sip_auth_uri" to "sip:2000@192.168.0.143:5060"
    Then "Alice" renews subscription with authentication to "Bob"
    Then pause for 1 seconds
    Then "Alice" unsubscribes from "Bob"
