#! /usr/bin/env python

from broadcastclient import BroadcastClient
import sys
import os
import re

class Shell:
	
	def __init__(self):
		self.bc = BroadcastClient()
		self.localcommands = ["help","ls","exit"]
		self.remoteCommands = {"find":"WANT","get":"DOWNLOAD"}
		

	def start_shell(self):
		runShell = True
		while runShell:
			useroption = raw_input("> ")
			if useroption in self.localcommands:
				if useroption == "ls":
					ls = os.listdir(os.getcwd())
					for f in ls:
						print f
				elif useroption == "exit":
					runShell = False
				elif useroption == "help":
					self._show_help()
			else:
				cmd_parts = self._parse_remote_cmd(useroption)
				if not len(cmd_parts):
					print "No such command!"
				else:
					cmd,desired_file = cmd_parts
					print cmd +" "+desired_file

	def _parse_remote_cmd(self,cmd):
		parts = re.split("\s+",cmd)
		if parts[0] not in self.remoteCommands:
			return []
		else:
			return [self.remoteCommands[parts[0]],parts[1]]

	def _show_help(self):
		print "The valid functions are:"
		for cmd in self.localcommands:
			print cmd

		for key in self.remoteCommands:
			print key+" <file name>"


if __name__ == "__main__":
	s = Shell()
	s.start_shell()