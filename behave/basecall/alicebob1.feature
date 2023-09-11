Feature: Alice Makes Calls

  Scenario: Alice calls Bob
    Given Alice uses Squirrel350 phone
    Given Bob uses Chipmunk5000 phone
    When Alice calls Bob
    Then Bob answers the phone
    And Alice talks for 10 seconds
    Then Bob hangs up the phone
    Then Alice phone receives hangup

  Scenario: Alice calls but Bob has DND set
    Given Alice uses Squirrel350 phone
    Given Bob uses Chipmunk5000 phone
      And status is set to DND
    When Alice calls Bob
    Then Alice talks for 10 seconds
    Then Alice hangs up the phone
    Then Bob has voicemail
