Feature: Presence Notification for Large Number of Users

  # Test setup: Provision 200 users according to the CSV, 1100-1299.
  @skip
  @import.presence/presence_users.csv
  Scenario: Large Number of Users Registers and Changes State
    Given extensions 1100 to 1299 register
    Then pause for 1 seconds
    Then many users subscribe to each other
    Then pause for 5 seconds
    Then "EvelynOsborne" sets presence to "After Hours"
    Then pause for 1 seconds
    Then "ShelleyMills" has received "After Hours" notification for "EvelynOsborne"
    Then "EvelynOsborne" sets presence to "Available"
    Then pause for 1 seconds
    Then in sequence users set presence to "After Hours"
    Then pause for 5 seconds
    Then in sequence users set presence to "Available"
    Then pause for 5 seconds
    Then many users unsubscribe from each other
