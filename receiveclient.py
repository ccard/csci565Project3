#! /usr/bin/env python
import socket
import struct

class ReceiveClient(object):

	UDP_IP = "239.6.6.6"
	UDP_PORT = 6666

	def __init__(self):
		super(ReceiveClient, self).__init__()

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
		while True:
			message,addr = self.sock.recvfrom(1024)
			print "Recieved: ", message


if __name__ == "__main__":
	rc = ReceiveClient()
	rc.listen()