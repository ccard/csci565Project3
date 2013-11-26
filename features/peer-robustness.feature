Feature: Central server is robust to peer failure
  As a server administrator
  If another peer goes down
  I don't want my server to crash

  Scenario: Peer goes down
    Given a running central server
    And a connected peer
    When the peer goes down
    Then the server is still running

