Feature: Calls are routed according to presence information
# Auto Attendant members: Dave
# Hunt Group members: Dave
# ACD Queue members: Dave

  Scenario: Ring to Dialed Extension
    Given Bob rings to Bob
    Given Bob is registered and waiting
    Then Bob lets phone ring 30 times before answering
    Then Alice rings Bob for 5 seconds
    Then Alice cancels the call
    Then Bob has missed a call

#  Scenario: Ring to Other Extension
#    Given Bob rings to Charlie
#    Given Bob unregisters
#    Given Charlie is registered and waiting
#    Then Alice calls Bob
#    Then pause for 10 seconds
#    Then Charlie's has missed a call
#    Then Bob's phone has not rung
#
#  Scenario: Ring to Auto Attendant
#    Given Bob rings to AutoAttendant
#    Given Bob is registered and waiting
#    Then Alice calls Bob
#    Then pause for 10 seconds
#    Then Dave's has missed a call
#    Then Bob's phone has not rung
#
#  Scenario: Ring to Hunt Group
#    Given Bob rings to HuntGroup
#    Given Bob is registered and waiting
#    Then Alice calls Bob
#    Then pause for 10 seconds
#    Then Dave's has missed a call
#    Then Bob's phone has not rung
#
#  Scenario: Ring to ACD Queue
#    Given Bob rings to ACDQueue
#    Given Bob is registered and waiting
#    Then Alice calls Bob
#    Then pause for 10 seconds
#    Then Dave's has missed a call
#    Then Bob's phone has not rung
#
#  Scenario: Ring to Extension and Extension (ring same ext twice)
#    Given Bob rings to Bob then Bob
#    Given Bob is registered and waiting
#    Then Alice calls Bob
#    Then pause for 10 seconds
#    Then Bob's has missed a call twice
#
#  Scenario: Ring to Extension and Other Extension
#    Given Bob rings to Bob and Charlie
#    Given Bob is registered and waiting
#    Given Charlie is registered and waiting
#    Then Alice calls Bob
#    Then pause for 10 seconds
#    Then Bob's has missed a call
#    Then Charlie's has missed a call
#
#  Scenario: Ring to Extension and Unregistered Extension
#    Given Bob rings to Bob and Charlie
#    Given Bob is registered and waiting
#    Given Charlie is unregistered
#    Then Alice calls Bob
#    Then pause for 10 seconds
#    Then Bob's has missed a call
#    Then Charlie's phone has not rung
#
#  Scenario: Ring to Extension and Auto Attendant (AA Ignored)
#    Given Bob rings to Bob then AutoAttendant
#    Given Bob is registered and waiting
#    Then Alice calls Bob
#    Then pause for 10 seconds
#    Then Bob's has missed a call
#    Then Dave's phone has not rung
#
#  Scenario: Ring to Extension and Hunt Group (HG Ignored)
#    Given Bob rings to Bob then HuntGroup
#    Given Bob is registered and waiting
#    Then Alice calls Bob
#    Then pause for 10 seconds
#    Then Bob's has missed a call
#    Then Dave's phone has not rung
#
#  Scenario: Ring to Extension and ACD Queue (expect ACD Queue Ignored)
#    Given Bob rings to Bob then ACDQueue
#    Given Bob is registered and waiting
#    Then Alice calls Bob
#    Then pause for 10 seconds
#    Then Bob's has missed a call
#    Then Dave's phone has not rung
#
#  Scenario: Ring to Other Extension and Dialed Extension
#    Given Bob rings to Charlie and Bob
#    Given Bob is registered and waiting
#    Then Alice calls Bob
#    Then pause for 10 seconds
#    Then Charlie's has missed a call
#    Then Bob's has missed a call
#
#  Scenario: Ring to Other Extension then Other Extension (ring same ext twice)
#    Given Bob rings to Charlie then Charlie
#    Given Charlie is registered and waiting
#    Then Alice calls Bob
#    Then pause for 10 seconds
#    Then Charlie's has missed a call twice
#
#  Scenario: Ring to Other Extension and Unregistered Other Extension
#    Given Bob rings to Charlie and Dave
#    Given Charlie is registered and waiting
#    Given Dave is unregistered
#    Then Alice calls Bob
#    Then pause for 10 seconds
#    Then Charlie's has missed a call
#    Then Dave's phone has not rung
#
#  Scenario: Ring to Other Extension and Auto Attendant
#    Given Bob rings to Charlie and AutoAttendant
#    Given Charlie is registered and waiting
#    Then Alice calls Bob
#    Then pause for 10 seconds
#    Then Charlie's has missed a call
#    Then Dave's has missed a call
#
#  Scenario: Ring to Other Extension and Hunt Group
#    Given Bob rings to Charlie and HuntGroup
#    Given Charlie is registered and waiting
#    Then Alice calls Bob
#    Then pause for 10 seconds
#    Then Bob's has missed a call
#    Then Dave's has missed a call
#
#  Scenario: Ring to Other Extension and ACD Queue
#    Given Bob rings to Charlie and ACDQueue
#    Given Charlie is registered and waiting
#    Then Alice calls Bob
#    Then pause for 10 seconds
#    Then Charlie's has missed a call
#    Then Dave's has missed a call
#
#  Scenario: Ring to Unregistered Other Extension and Extension
#    Given Bob rings to Charlie and Bob
#    Given Bob is registered and waiting
#    Given Charlie is unregistered
#    Then Alice calls Bob
#    Then pause for 10 seconds
#    Then Bob's has missed a call
#    Then Charlie's phone has not rung
#
#  Scenario: Ring to Unregistered Other Extension and Unregistered Other Extension
#    Given Bob rings to Charlie and Dave
#    Given Charlie is registered and waiting
#    Given Dave is unregistered
#    Then Alice calls Bob
#    Then pause for 10 seconds
#    Then Charlie's phone has not rung
#    Then Dave's phone has not rung
#
#  Scenario: Ring to Unregistered Other Extension and Auto Attendant
#    Given Bob rings to Charlie and AutoAttendant
#    Given Bob is registered and waiting
#    Given Dave is registered and waiting
#    Then Alice calls Bob
#    Then pause for 10 seconds
#    Then Dave's has missed a call
#    Then Charlie's phone has not rung
#
#  Scenario: Ring to Unregistered Other Extension and Hunt Group
#    Given Bob rings to Charlie and HuntGroup
#    Given Bob is registered and waiting
#    Given Dave is registered and waiting
#    Then Alice calls Bob
#    Then pause for 10 seconds
#    Then Dave's has missed a call
#    Then Charlie's phone has not rung
#
#  Scenario: Ring to Unregistered Other Extension and ACD Queue
#    Given Bob rings to Charlie and ACDQueue
#    Given Bob is registered and waiting
#    Then Alice calls Bob
#    Then pause for 10 seconds
#    Then Charlie's phone has not rung
#    Then Dave's has missed a call
#
#  Scenario: Ring to Auto Attendant and Extension
#    Given Bob rings to AutoAttendant and Bob
#    Given Bob is registered and waiting
#    Given Dave is registered and waiting
#    Then Alice calls Bob
#    Then pause for 10 seconds
#    Then Dave's has missed a call
