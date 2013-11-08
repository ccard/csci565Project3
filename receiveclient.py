#! /usr/bin/env python
import socket
import struct
import json

class ReceiveClient(object):

	def __init__(self,address="239.6.6.6",port=6666):
		super(ReceiveClient, self).__init__()

		self.UDP_IP,self.UDP_PORT = [address,port]

		self.sock = socket.socket(socket.AF_INET,
								socket.SOCK_DGRAM,
								socket.IPPROTO_UDP)

		self.sock.setsockopt(socket.SOL_SOCKET, 
							socket.SO_REUSEADDR,1)

		self.sock.bind(('',self.UDP_PORT))

		mreq = struct.pack("=4sl",
							socket.inet_aton(self.UDP_IP),
							socket.INADDR_ANY)

		self.sock.setsockopt(socket.IPPROTO_IP,socket.IP_ADD_MEMBERSHIP,
							mreq)

	
	def listen(self):
		message,addr = self.sock.recvfrom(1024)
		print "received"
		return json.loads(message)


if __name__ == "__main__":
	rc = ReceiveClient()
	rc.listen()