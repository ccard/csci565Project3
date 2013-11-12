#! /usr/bin/env python
import socket
import json

class BroadcastClient(object):

	
	def __init__(self,address="239.6.6.6",port=6666):
		super(BroadcastClient, self).__init__()

		self.UDP_IP,self.UDP_PORT = [address,port]

		self.sock = socket.socket(socket.AF_INET,
								socket.SOCK_DGRAM,
								socket.IPPROTO_UDP)

		self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL,
							2)

	
	def send_request(self,verb="WANT",filename="NOTHING"):
		self.sock.sendto(json.dumps({"VERB":verb,"FILE":filename}),(self.UDP_IP,
							self.UDP_PORT))
		message,addr = self.sock.recvfrom(self.UDP_PORT)
		return json.loads(message)

if __name__ == "__main__":
	bc = BroadcastClient()
	bc.send_request("WANT","socat_broadcast.sh")
