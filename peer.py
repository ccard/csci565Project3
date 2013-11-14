#! /usr/bin/env python

import os
import errno
import sys
import json
import time
import threading
import stat

from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
from twisted.web.static import File
from twisted.web.server import Site

from os.path import realpath
from sys import argv, exit

from fuse import FUSE, FuseOSError, Operations, LoggingMixIn, fuse_get_context


class NapsterFilesystem(Operations):

    """
    Essentially a union filsystem between a local directory and the
    central server.

    The files shown in this FUSE-mounted directory are the union of local files
    and peer-hosted files.  When a non-local file is downloaded, it's cached in
    the local directory for future reads, as well as becoming shared from this
    host.

    File writes are unsupported, though any changes to the local directory will
    be reflected in this directory.
    """

    def __init__(self, local):
        self.local = realpath(local)

        self.created = time.time()

    # redirect all FUSE events to the same event with filenames scoped
    # under the local directory, i.e. loopfs
    # def __call__(self, op, path, *args):
        # return super(NapsterFilesystem, self).__call__(
                # op, self.local + path, *args)

    def getattr(self, path, fh):
        if path == '/':
            uid, gid, _ = fuse_get_context()
            return dict(st_mode=(stat.S_IFDIR | 0444),
                        st_ctime=self.created,
                        st_mtime=self.created,
                        st_atime=self.created,
                        st_uid=uid,
                        st_gid=gid,
                        st_nlink=2)
        else:
            # TODO download remote if exists

            # proxy to local
            if os.path.exists(self.local + path):
                st = os.lstat(self.local + path)
                return dict((key, getattr(st, key)) for key in (
                    'st_atime', 'st_ctime', 'st_gid', 'st_mode',
                    'st_mtime', 'st_nlink', 'st_size', 'st_uid'))
            else:
                raise FuseOSError(errno.ENOENT)

    # TODO cache files back in local directory if remote
    def open(self, path, flags):
        return os.open(self.local + path, flags)

    def read(self, path, size, offset, fh):
        # file handle is from os.open in `open`, so use it directly
        os.lseek(fh, offset, 0)
        return os.read(fh, size)

    # TODO union with central server file list
    def readdir(self, path, fh):
        return ['.', '..'] + os.listdir(self.local + path)

    def release(self, path, fh):
        # file handle is real, use it
        return os.close(fh)


class Peer(DatagramProtocol):

    UDP_IP = "239.6.6.6"
    UDP_PORT = 6666
    UDP_PORTSend = 6667

    def startProtocol(self):
        # Set the TTL>1 so multicast will cross router hops:
        self.transport.setTTL(5)
        # Join a specific multicast group:
        self.transport.joinGroup(self.UDP_IP)

    def datagramReceived(self, datagram, address):
        print "Datagram %s received from %s, %f" % (repr(datagram),
                                                    repr(address),
                                                    time.clock())
        msg = json.loads(datagram)
        if msg["VERB"] == 'WANT' or msg["VERB"] == 'DOWNLOAD':
            files = os.listdir(os.getcwd())
            if msg["FILE"] in files:
                res = self.compile_message("HAVE", msg["FILE"])
                self.transport.write(res, (self.UDP_IP, self.UDP_PORTSend))

    def compile_message(self, verb, filename):
        return json.dumps({"VERB": verb, "FILE": filename})

    def statfs(self, path):
        return dict(f_bsize=512, f_blocks=4096, f_bavail=2048)

if __name__ == "__main__":
    if len(argv) != 3:
        print('usage: %s <local directory> <mountpoint>' % argv[0])
        exit(1)

    local = argv[1]
    mountpoint = argv[2]

    peer = Peer()

    # Legacy: respond to UDP multicast protocol
    # We use listenMultiple=True so that we can run
    # multiple peers on the same machine
    reactor.listenMulticast(6666, Peer(),
                            listenMultiple=True)

    # serve files from the local directory over HTTP
    # TODO subclass Site to add count of open connections to be able to
    # track "load" as defined by the project. Will also need to
    # do callFromThread from the FUSE stuff in order to track downloads.
    resource = File(realpath(local))
    factory = Site(resource)
    reactor.listenTCP(6666, factory)

    print "Starting HTTP file server..."

    # run reactor in separate thread, since FUSE is going to
    # block the main thread
    t = threading.Thread(target=reactor.run, args=(False,))
    t.start()

    print "File server started."
    print "Now starting FUSE filesystem..."

    # run fuse main loop, this will block until unmounted or killed
    FUSE(NapsterFilesystem(local), mountpoint, foreground=True)

    print "FUSE received shutdown signal, shutting down reactor..."

    reactor.callFromThread(reactor.stop)

    print "bye!"
