#! /usr/bin/env python
from broadcastclient import BroadcastClient
from receiveclient import ReceiveClient
import sys
import json

class Peer(object):
	
	UDP_IP = "239.6.6.6"
	UDP_PORT = 6666

	def __init__(self):
		super(Peer, self).__init__()

		self.listener = ReceiveClient(self.UDP_IP,self.UDP_PORT)
		self.broadcast = BroadcastClient(self.UDP_IP,self.UDP_PORT)
		
	def listen(self):
		while True:
			request = self.listener.listen()
			print request["VERB"]
			print request["FILE"]

	def query(self):
		self.broadcast.send_request()

if __name__ == "__main__":
	peer = Peer()
	if len(sys.argv) > 1:
		peer.listen()
	else:
		peer.query()