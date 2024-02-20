Feature: Calls are Transferred Between Endpoints

  # Setup: Alice is caller
  # Bob is assigned to Hunt and ACD
  # Bob has logged into the UI and set ACD status as Available
  # Charlie receives calls

  Scenario: Call is Trasnferred
    Given "Alice" registers
    Given "Bob" registers
    Given "Charlie" registers
    Then pause for 1 seconds
    Then "Bob" expects a call
    Then "Charlie" expects a call
    Then "Alice" calls "H100"
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
    Then "Bob" expects a call
    Then "Alice" calls "H100"
    Then "Bob" answers the call
    Then pause for 5 seconds
    Then "Bob" hangs up

  Scenario: Caller to Hunt Group, Answered, Xfer to Ext
    Given "Alice" registers
    Given "Bob" registers
    Given "Charlie" registers
    Then pause for 1 seconds
    Then "Bob" expects a call
    Then "Charlie" expects a call
    Then "Alice" calls "H100"
    Then "Bob" answers the call
    Then pause for 5 seconds
    Then "Bob" transfers to "Charlie"
    Then "Charlie" answers the call
    Then pause for 5 seconds
    Then "Charlie" hangs up

  @skip
  # Need four endpoints, separate agent for ACD
  Scenario: Caller to Hunt Group, Answered, Xfer to ACD, Answered
    Given "Alice" registers
    Given "Bob" registers
    Given "Charlie" registers
    Then pause for 1 seconds
    Then "Bob" expects a call
    Then "Charlie" expects a call
    Then "Alice" calls "H100"
    Then "Bob" answers the call
    Then pause for 5 seconds
    Then "Bob" transfers to "A200"
    Then "Bob" expects a call
    Then pause for 5 seconds
    Then "Bob" hangs up

  Scenario: Caller to ACD, Answered
    Given "Alice" registers
    Given "Bob" registers
    Then pause for 1 seconds
    Then "Bob" expects a call
    Then "Alice" calls "A200"
    Then "Bob" answers the call
    Then pause for 5 seconds
    Then "Bob" hangs up

  Scenario: Caller to ACD, Answered, Xfer to Ext
    Given "Alice" registers
    Given "Bob" registers
    Given "Charlie" registers
    Then pause for 1 seconds
    Then "Bob" expects a call
    Then "Alice" calls "A200"
    Then "Bob" answers the call
    Then pause for 5 seconds
    Then "Charlie" expects a call
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
    Then "Bob" expects a call
    Then "Charlie" expects a call
    Then "Alice" calls "A200"
    Then "Bob" answers the call
    Then pause for 5 seconds
    Then "Bob" transfers to "H100"
    Then "Charlie" answers the call
    Then pause for 5 seconds
    Then "Charlie" hangs up
