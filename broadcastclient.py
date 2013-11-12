#! /usr/bin/env python
import socket
import json
import re
import os
import time
import sys
import struct
import requests
import StringIO


class BroadcastClient(object):

    def __init__(self, latencies, address="239.6.6.6", sendport=6666, recvport=6667):
        super(BroadcastClient, self).__init__()

        self.lat = {}
        for (host1, host2, latency) in latencies:
            print (host1, host2, latency)
            addr1 = socket.gethostbyname(host1)
            addr2 = socket.gethostbyname(host2)
            if addr1 not in self.lat: self.lat[addr1] = {}
            self.lat[addr1][addr2] = latency
            self.lat[addr1][addr1] = 0
            if addr2 not in self.lat: self.lat[addr2] = {}
            self.lat[addr2][addr1] = latency
            self.lat[addr2][addr1] = latency
            self.lat[addr2][addr2] = 0

        print self.lat
        
        self.UDP_IP, self.UDP_PORT, self.UDP_PORTRecv = [
            address, sendport, recvport]

        self.socksend = socket.socket(socket.AF_INET,
                                      socket.SOCK_DGRAM,
                                      socket.IPPROTO_UDP)
        self.sockrecv = socket.socket(socket.AF_INET,
                                      socket.SOCK_DGRAM,
                                      socket.IPPROTO_UDP)

        self.socksend.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL,
                                 2)
        self.sockrecv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sockrecv.bind(('', self.UDP_PORTRecv))

        mreq = struct.pack("=4sl",
                           socket.inet_aton(self.UDP_IP),
                           socket.INADDR_ANY)

        self.sockrecv.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP,
                                 mreq)
        self.sockrecv.settimeout(.3)

    def send_request(self, verb="WANT", filename="NOTHING"):
        self.socksend.sendto(
            json.dumps({"VERB": verb, "FILE": filename}), (self.UDP_IP,
                                                           self.UDP_PORT))
        i = 0
        res = []
        while i < 3 :
            message, (addr, port) = self.sockrecv.recvfrom(1024)
            res.append({"message" : message, "address" : addr})
            i += 1
            print message

        response = json.loads(message)
        if verb == "DOWNLOAD" and response["VERB"] == "HAVE":
            self._download_file(res,filename)

    def _download_file(self,response,filename):
        me = socket.gethostbyname(socket.gethostname())
        print me
        print self.lat
        print [msg["address"] for msg in response]
        best_host = min(response, key=lambda msg: self.lat[me][msg["address"]])
        latency = self.lat[me][best_host]
        print best_host
        f = requests.get("http://%s:6666/%s" % (best_host, response["FILE"]))
        if f.status_code == 200:
            writer = open(filename, 'w')
            writer.write(f.content)
            writer.close()
            host = socket.gethostbyaddr(address[0])

            time.sleep(latency)
            print "Download of %s completed in %s seconds!" % (filename, latency)
        else:
            print "Error downloading file"
            dir(f)
if __name__ == "__main__":
    bc = BroadcastClient()
    bc.send_request("WANT", "socat_broadcast.sh")
