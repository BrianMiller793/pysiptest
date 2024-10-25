Feature: Alice Makes Calls

  Scenario: Alice calls Bob
    Given Alice1 registers
    Given Bob1 registers

    Then pause for 1 seconds
    Then connect to server UC event socket
#    Then pause for 1 seconds
    Then Bob1 expects a call
    Then Alice1 calls Bob1
    Then Bob1 answers the call
    Then pause for 1 seconds
    Then get channel info for current calls
    Then send 8 INFO to caller
    Then pause for 10 seconds
    Then Bob1 hangs up
    Then pause for 5 seconds

    Then Bob1 expects a call
    Then Alice1 calls Bob1
    Then Bob1 answers the call
    Then pause for 1 seconds
    Then get channel info for current calls
    Then send 99 INFO to caller
    Then pause for 65 seconds
    Then stop event background task
    Then Alice1 hangs up
    Then pause for 5 seconds

    # Pausing for registration timeout
    Then Bob1 expects a call
    Then Alice1 calls Bob1
    Then Bob1 answers the call
    Then pause for 1 seconds
    Then get channel info for current calls
    Then send 99 INFO to caller
    Then pause for 15 seconds
    Then Alice1 registers
    Then Bob1 registers
    Then pause for 100 seconds
    Then stop event background task
    Then Bob1 hangs up
    Then pause for 1 seconds
    Then Alice1 unregisters
    Then Bob1 unregisters
