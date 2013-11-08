#! /usr/bin/env python

from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
import sys
import json
import os

class Peer(DatagramProtocol):
    
    UDP_IP = "239.6.6.6"
    UDP_PORT = 6666
        
    def startProtocol(self):
        # Set the TTL>1 so multicast will cross router hops:
        self.transport.setTTL(5)
        # Join a specific multicast group:
        self.transport.joinGroup(self.UDP_IP)
                    

    def datagramReceived(self,datagram, address):
        print "Datagram %s received from %s" % (repr(datagram), repr(address))
        msg = json.loads(datagram)
        if msg["VERB"] == 'WANT':
            files = os.listdir(os.getcwd())
            if msg["FILE"] in files:
                res = self.compile_message("HAVE",msg["FILE"])
                self.transport.write(res, (self.UDP_IP, self.UDP_PORT))

    def compile_message(self,verb,filename):
        return json.dumps({"VERB": verb, "FILE": filename})

if __name__ == "__main__":
    peer = Peer()
    # We use listenMultiple=True so that we can run
    # multiple peers on the same machine
    reactor.listenMulticast(6666, Peer(),
                        listenMultiple=True)
    reactor.run()