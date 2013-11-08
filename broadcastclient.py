#! /usr/bin/env python
import socket
import json

class BroadcastClient(object):

	UDP_IP = "239.6.6.6"
	UDP_PORT = 6666

	
	def __init__(self):
		super(BroadcastClient, self).__init__()

		self.sock = socket.socket(socket.AF_INET,
								socket.SOCK_DGRAM,
								socket.IPPROTO_UDP)

		self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL,
							2)

	
	def send_request(self,verb="WANT",filename="NOTHING"):
		self.sock.sendto(json.dumps({"VERB":verb,"FILE":filename}),(self.UDP_IP,
							self.UDP_PORT))

if __name__ == "__main__":
	bc = BroadcastClient()
	bc.send_request()