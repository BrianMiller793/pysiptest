# pysiptest
Python SIP test framework

`pysiptest` is a Behave-driven framework for testing SIP scenarios.  It's
designed to model a SIP client, behaving as an endpoint device.  The
tests are written to model the behavior of a specific device, allowing
emulation of devices in complex multi-caller scenarios.

Example:

    Feature: Alice Makes Calls

      Scenario: Alice calls Bob
        Given Alice uses Squirrel350 phone
        Given Bob uses Chipmunk5000 phone
        When Alice calls Bob
        Then Bob answers the phone
        And Alice and Bob talk for 10 seconds
        Then Bob hangs up the phone
        Then Alice receives BYE

      Scenario: Alice calls but Bob has DND set
        Given Alice uses Squirrel350 phone
        Given Bob uses Chipmunk5000 phone
          And Status is set to DND
        When Alice calls Bob
        Then Alice talks to voicemail for 10 seconds
        Then Alice hangs up the phone
        Then Bob has voicemail waiting

The Python step files contain functions implementing set up of the
test environment and the user actions.  This allows the test to take
action unavailable to SIPp, such as accessing APIs or databases.

Copyright &copy; 2018-2022 Brian C. Miller<br>
Open source license GNU General Public License version 3

RFCs:
RFC 2543
RFC 2616
RFC 2617
RFC 3261
RFC 3262
RFC 3265
RFC 3311
RFC 3428
RFC 3515
RFC 3903
RFC 5626
RFC 5839
RFC 6026
RFC 6086
RFC 6141
RFC 6878
RFC 7614
RFC 7616 (TODO)
RFC 7621

