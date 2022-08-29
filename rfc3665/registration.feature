Feature: Registration, RFC 3665, Section 2

  @wip
  Scenario: 2.5 Unsuccessful Registration
    Given new connection with user "Bob" and server "Biloxi"
    When "Bob" sends request REGISTER
    Then "Bob" receives response "401,403,407"
    When "Bob" sends request REGISTER
      And with header field Authorization for "NoSuchUser"
    Then "Bob" receives response "401,403,407"

  @wip
  Scenario: 2.1 Successful new Registration
    Given new connection with user "Bob" and server "Biloxi"
    When "Bob" sends request REGISTER
    Then "Bob" receives response "401,407"
    When "Bob" sends request REGISTER
      And with header field Authorization for "Bob"
    Then "Bob" receives response "200"
    Then "Bob" is registered at the server

  @skip
  Scenario: 2.3 Request for Current Contact List
    Given existing connection with user "Bob" and server "Biloxi"
    When "Bob" sends request REGISTER
      And without header field "Contact"
    Then "Bob" receives response "401,407"
    When "Bob" sends request REGISTER
      And without header field "Contact"
      And with header field Authorization for "Bob"
    Then "Bob" receives response "200"
    Then "Bob" response contains "Contact" field, value "sip:2004"

  @wip
  Scenario: 2.2 Update of Contact List
    Given existing connection with user "Bob" and server "Biloxi"
    When "Bob" sends request REGISTER
      And with header field "Contact" value "mailto:bob@biloxi.example.com"
    Then "Bob" receives response "401,407"
    When "Bob" sends request REGISTER
      And with header field "Contact" value "mailto:bob@biloxi.example.com"
      And with header field Authorization for "Bob"
    Then "Bob" receives response "200"
    Then "Bob" response contains "Contact" field, value "mailto:bob@biloxi.example.com"

  @wip
  Scenario: 2.4 Cancellation of Registration
    Given existing connection with user "Bob" and server "Biloxi"
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

