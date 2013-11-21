Feature: Request file
	In order to find available files
	As file sharer
	We'll query the server

	Scenario: Request available files
		Given running central server
		And peer hosting files
		When I can connect to the central server
		Then I see that peers files

	Scenario: Download uncorrupted file
		Given running central server
		And peer hosting files
		When I can connect to the central server
		Then I see that peers files
		Then see if I can open the file