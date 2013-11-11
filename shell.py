#! /usr/bin/env python

from broadcastclient import BroadcastClient
import sys
import os

class Shell:
	
	def __init__(self):
		self.bc = BroadcastClient()
		self.commands = {"find" : "WANT","get" : "DOWNLOAD",
					"ls" : "ls","exit":"exit"]	
		

	def startShell(self):
		runShell = True
		while runShell:
			useroption = raw_input("> ")
			if useroption in self.commands:
				print "valid option"




if __name__ == "__main__":
	startShell()