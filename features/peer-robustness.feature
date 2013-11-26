Feature: Peers are robust to failure
  As a file sharer
  If another peer or the central server goes down
  I don't want my own peer to crash

  Background:
    Given a running central server

  Scenario: Server goes down
    Given I launch my own peer
    When the server goes down
    Then my peer is still running

  Scenario: Another peer goes down
    Given another peer hosting files
    And I launch my own peer
    When the other peer goes down
    Then my peer is still running

