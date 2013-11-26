Feature: Share Files
  As a file sharer
  In order to upload and download files
  We'll connect our peer to the network

  Background:
    Given a running central server

  Scenario: List available files
    Given another peer hosting files
    When I launch my own peer
    Then I see that peer's files

  Scenario: Download remote file
    Given another peer hosting files
    When I launch my own peer
    Then I can download and read the remote file

  Scenario: Share file
    Given I launch a peer sharing a file
    When another peer connects
    Then they can download and read my file



