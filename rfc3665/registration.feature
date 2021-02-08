Feature: Registration, RFC 3665, Section 2

  Scenario: 2.1 Successful new Registration
    Given new connection with user "Bob" and server "Biloxi"
      when "Bob" sends request "REGISTER"
      then "Bob" receives response "401,407"
      when "Bob" sends request "REGISTER"
        and with header field "Authorization"
      then "Bob" receives response "200"
      then "Bob" is registered at the server

  Scenario: 2.2 Update of Contact List
    Given existing connection with user "Bob" and server "Biloxi"
      when "Bob" sends request "REGISTER"
        and with header field "Authorization"
        and with header field "Contact: mailto:bob@biloxi.example.com"
      then "Bob" receives response "200"
      then "Bob" response contains field "Contact: mailto:bob@biloxi.example.com"

  Scenario: 2.3 Request for Current Contact List
    Given existing connection with user "Bob" and server "Biloxi"
      when "Bob" sends request "REGISTER"
        and with header field "Authorization"
        and without header field "Contact"
      then "Bob" receives response "200"
      then "Bob" response contains field "Contact"

  Scenario: 2.4 Cancellation of Registration
    Given existing connection with user "Bob" and server "Biloxi"
      when "Bob" sends request "REGISTER"
        and with header field "Authorization"
        and with header field "Expires: 0"
        and with header field "Contact: *"
      then "Bob" receives response "200"
      then "Bob" response does not contain field "Contact"
      then "Bob" is unregistered

  Scenario: 2.5 Unsuccessful Registration
    Given new connection with user "Bob" and server "Biloxi"
      when "Bob" sends request "REGISTER"
      then "Bob" receives response "401,407"
      when "Bob" sends request "REGISTER"
        and with password "bad password"
        and with header field "Authorization"
      then "Bob" receives response "401,407"

