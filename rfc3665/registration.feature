Feature: Registration, RFC 3665, Section 2

  @wip
  Scenario: 2.1 Successful new Registration
    Given new connection with user "Bob" and server "Docker"
    When "Bob" sends request REGISTER
    Then "Bob" receives response "401,407"
    When "Bob" sends request REGISTER
      And with header field Authorization for "Bob"
    Then "Bob" receives response "200"
    Then "Bob" is registered at the server

  @wip
  Scenario: 2.1a Successful new Registration
    Given new connection with user "Alice" and server "Docker"
    When "Alice" sends request REGISTER
    Then "Alice" receives response "401,407"
    When "Alice" sends request REGISTER
      And with header field Authorization for "Alice"
    Then "Alice" receives response "200"
    Then "Alice" is registered at the server

  @wip
  Scenario: Calls through UCM
  Given "Alice" waits for a call
  When "Bob" calls "Alice"
    And "Bob" makes the call
  Then "Alice" answers the call
  Then pause for 5 seconds
  Then "Bob" ends the call
  Then "Alice" receives "BYE"

  @skip
  Scenario: 2.3 Request for Current Contact List
    Given existing connection with user "Bob" and server "Docker"
    When "Bob" sends request REGISTER
      And without header field "Contact"
    Then "Bob" receives response "401,407"
    When "Bob" sends request REGISTER
      And without header field "Contact"
      And with header field Authorization for "Bob"
    Then "Bob" receives response "200"
    Then "Bob" response contains "Contact" field, value "sip:2004"

  @skip
  Scenario: 2.2 Update of Contact List
    Given existing connection with user "Bob" and server "Docker"
    When "Bob" sends request REGISTER
      And with header field "Contact" value "mailto:bob@biloxi.example.com"
    Then "Bob" receives response "401,407"
    When "Bob" sends request REGISTER
      And with header field "Contact" value "mailto:bob@biloxi.example.com"
      And with header field Authorization for "Bob"
    Then "Bob" receives response "200"
    Then "Bob" response contains "Contact" field, value "mailto:bob@biloxi.example.com"

  @wip
  Scenario: 2.4 Cancellation of Registration for BobD
    Given existing connection with user "Bob" and server "Docker"
    When "Bob" sends request REGISTER
      And with Contact field expires 0
      And with header field "Expires" value "0"
    Then "Bob" receives response "401,407"
    When "Bob" sends request REGISTER
      And with Contact field expires 0
      And with header field "Expires" value "0"
      And with header field Authorization for "Bob"
    Then "Bob" receives response "200"
    Then "Bob" response does not contain field "Contact"
    Then "Bob" is unregistered

  @wip
  Scenario: 2.4 Cancellation of Registration for AliceD
    Given existing connection with user "Alice" and server "Docker"
    When "Alice" sends request REGISTER
      And with Contact field expires 0
      And with header field "Expires" value "0"
    Then "Alice" receives response "401,407"
    When "Alice" sends request REGISTER
      And with Contact field expires 0
      And with header field "Expires" value "0"
      And with header field Authorization for "Alice"
    Then "Alice" receives response "200"
    Then "Alice" response does not contain field "Contact"
    Then "Alice" is unregistered

