Feature: Download remote files
	As a file sharer
	In order to download available files
	We'll connect our peer to the network

	Scenario: List available files
		Given a running central server
		And another peer hosting files
		When I launch my own peer
		Then I see that peer's files

	Scenario: Download remote file
		Given a running central server
		And another peer hosting files
		When I launch my own peer
		Then I can download and read the remote file
