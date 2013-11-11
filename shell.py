#! /usr/bin/env python

from broadcastclient import BroadcastClient
import sys
import os

class Shell:
	
	def __init__(self):
		self.bc = BroadcastClient()
		self.commands = {"find" : "WANT","get" : "DOWNLOAD",
					"ls" : "ls","exit":"exit"}
		

	def startShell(self):
		runShell = True
		while runShell:
			useroption = raw_input("> ")
			if useroption in self.commands:
				print "valid option"
				temp = self.commands[useroption]
				if temp == "ls":
					print os.listdir(os.getcwd())
				elif temp == "exit":
					runShell = False
			else:
				print "No such command!"




if __name__ == "__main__":
	s = Shell()
	s.startShell()