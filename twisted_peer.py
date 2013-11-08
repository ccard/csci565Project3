#!/usr/bin/env python
from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
import json
import os

class NapsterPeer(DatagramProtocol):

    def startProtocol(self):
        """
        Called after protocol has started listening.
        """
        # Set the TTL>1 so multicast will cross router hops:
        self.transport.setTTL(5)
        # Join a specific multicast group:
        self.transport.joinGroup("239.6.6.6")

    def datagramReceived(self, datagram, address):
        print "Datagram %s received from %s" % (repr(datagram), repr(address))
        msg = json.loads(datagram)
        if msg["VERB"] == 'WANT':
            files = os.listdir(os.getcwd())
            if msg["FILE"] in files:
                res = json.dumps({"VERB": "HAVE", "FILE": msg["FILE"]})
                self.transport.write(res, ("239.6.6.6", 6666))

# We use listenMultiple=True so that we can run
# multiple peers on the same machine
reactor.listenMulticast(6666, NapsterPeer(),
                        listenMultiple=True)
reactor.run()
