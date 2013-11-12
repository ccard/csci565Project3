#! /usr/bin/env python
import socket
import json
import struct
import requests
import StringIO

class BroadcastClient(object):

	
	def __init__(self,address="239.6.6.6",sendport=6666,recvport=6667):
		super(BroadcastClient, self).__init__()

		self.UDP_IP,self.UDP_PORT,self.UDP_PORTRecv = [address,sendport,recvport]

		self.socksend = socket.socket(socket.AF_INET,
								socket.SOCK_DGRAM,
								socket.IPPROTO_UDP)
		self.sockrecv = socket.socket(socket.AF_INET,
								socket.SOCK_DGRAM,
								socket.IPPROTO_UDP)

		self.socksend.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL,
							2)
		self.sockrecv.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
		self.sockrecv.bind(('',self.UDP_PORTRecv))

  		mreq = struct.pack("=4sl",
            socket.inet_aton(self.UDP_IP),
            socket.INADDR_ANY)

  		self.sockrecv.setsockopt(socket.IPPROTO_IP,socket.IP_ADD_MEMBERSHIP,
            mreq)

	
	def send_request(self,verb="WANT",filename="NOTHING"):
		self.socksend.sendto(json.dumps({"VERB":verb,"FILE":filename}),(self.UDP_IP,
							self.UDP_PORT))
		message,addr = self.sockrecv.recvfrom(1024)
		response = json.loads(message)
		if verb == "DOWNLOAD" and response["VERB"] == "HAVE":
			f = requests.get("http://%s:6666/%s" % (addr[0],response["FILE"]))
			if f.status_code == 200:
				writer = open(filename,'w')
				writer.write(f.content);
			else:
				print "Error downloading file"
				dir(f)
		return json.loads(message)

if __name__ == "__main__":
	bc = BroadcastClient()
	bc.send_request("WANT","socat_broadcast.sh")
