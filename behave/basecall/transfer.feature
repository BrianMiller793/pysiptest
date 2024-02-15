Feature: Calls are Transferred Between Endpoints

  Scenario: Call is Trasnferred
    Given "Alice" registers
    Given "Bob" registers
    Given "Charlie" registers
    Then pause for 1 seconds
    Then "Bob" waits for a call
    Then "Alice" calls "Bob"
    Then "Bob" answers the call
    Then pause for 5 seconds
    Then "Bob" transfers to "Charlie"
    Then "Charlie" answers the call
    Then pause for 5 seconds
    Then "Charlie" hangs up

  Scenario: Caller to Hunt Group, Answered
    Given "Alice" registers
    Given "Bob" registers
    Then pause for 1 seconds
    Then "Bob" waits for a call
    Then "Alice" calls "Bob"
    Then "Bob" answers the call
    Then pause for 5 seconds
    Then "Bob" hangs up

  @skip
  Scenario: Caller to Hunt Group, Answered, Xfer to Ext
    Given "Alice" registers
    Given "Bob" registers
    Given "Charlie" registers
    Then pause for 1 seconds
    Then "Bob" waits for a call
    Then "Alice" calls "100"
    Then "Bob" answers the call
    Then pause for 5 seconds
    Then "Bob" transfers to "Charlie"
    Then "Charlie" answers the call
    Then pause for 5 seconds
    Then "Charlie" hangs up

  @skip
  Scenario: Caller to Hunt Group, Answered, Xfer to ACD, Answered
    Given "Alice" registers
    Given "Bob" registers
    Given "Charlie" registers
    Then pause for 1 seconds
    Then "Bob" waits for a call
    Then "Alice" calls "100"
    Then "Bob" answers the call
    Then pause for 5 seconds
    Then "Bob" transfers to "200"
    Then "Charlie" answers the call
    Then pause for 5 seconds
    Then "Charlie" hangs up

  Scenario: Caller to ACD, Answered
    Given "Alice" registers
    Given "Bob" registers
    Then pause for 1 seconds
    Then "Bob" waits for a call
    Then "Alice" calls "200"
    Then "Bob" answers the call
    Then pause for 5 seconds
    Then "Bob" hangs up

  @skip
  Scenario: Caller to ACD, Answered, Xfer to Ext
    Given "Alice" registers
    Given "Bob" registers
    Given "Charlie" registers
    Then pause for 1 seconds
    Then "Bob" waits for a call
    Then "Alice" calls "200"
    Then "Bob" answers the call
    Then pause for 5 seconds
    Then "Bob" transfers to "Charlie"
    Then "Charlie" answers the call
    Then pause for 5 seconds
    Then "Charlie" hangs up

  @skip
  Scenario: Caller to ACD, Answered, Xfer to Hunt Group, Answered
    Given "Alice" registers
    Given "Bob" registers
    Given "Charlie" registers
    Then pause for 1 seconds
    Then "Bob" waits for a call
    Then "Alice" calls "200"
    Then "Bob" answers the call
    Then pause for 5 seconds
    Then "Bob" transfers to "100"
    Then "Charlie" answers the call
    Then pause for 5 seconds
    Then "Charlie" hangs up
