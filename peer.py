#! /usr/bin/env python
import logging
import os
import errno
import socket
import time
import threading
import stat
import json
from os.path import realpath
from sys import argv, exit
from logging.config import dictConfig

import requests
import treq
from twisted.internet import reactor, task
from twisted.web.static import File
from twisted.web.server import Site
from fuse import FUSE, FuseOSError, Operations, fuse_get_context

dictConfig({
    'version': 1,

    'formatters': {
        'colored': {
            '()': 'colorlog.ColoredFormatter',
            'format': "%(log_color)s%(asctime)s %(levelname)-8s %(message)s",
            'datefmt': "%H:%M:%S",
        }
    },

    'handlers': {
        'stream': {
            'class': 'logging.StreamHandler',
            'formatter': 'colored',
        },
    },

    'loggers': {
        'default': {
            'handlers': ['stream'],
            'level': 'DEBUG',
        },
    },
})

log = logging.getLogger("default")


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

    def __init__(self, local_dir):
        self.local = realpath(local_dir)

        self.created = time.time()
        self.central_server = "localhost:6667"

        self.central_files = self.get_central_files()
        self.last_fetched = time.time()


    def get_central_files(self):
        try:
            files = requests.get('http://%s/' % self.central_server)
        except requests.ConnectionError as e:
            log.warn("Couldn't get files from central server: %s" % e)
            return {}
        if files.status_code is not 200:
            log.warn("Couldn't get files from central server: %s" % files)
            return {}
        else:
            files = files.json()
            log.info("Received files from central server: %s", files)
            return files

    #noinspection PyMethodOverriding
    def getattr(self, path, fd):
        log.debug("getattr on %s" % path)
        uid, gid, _ = fuse_get_context()
        if path == '/':
            return dict(st_mode=(stat.S_IFDIR | 0o444),
                        st_ctime=self.created,
                        st_mtime=self.created,
                        st_atime=self.created,
                        st_uid=uid,
                        st_gid=gid,
                        st_nlink=2)
        else:
            log.debug("trying getattr %s locally..." % path)
            try:
                st = os.lstat(self.local + path)
                return dict((key, getattr(st, key)) for key in (
                    'st_atime', 'st_ctime', 'st_gid', 'st_mode',
                    'st_mtime', 'st_nlink', 'st_size', 'st_uid'))
            except IOError:
                log.info("File %s doesn't exist locally..." % path)
                pass

            # try getting remote

            # TODO download remote if exists
            filename = path[1:]
            if filename in self.central_files:
                log.debug("File %s exists on central server...", filename)
                return dict(st_mode=(stat.S_IFREG | 0o444),
                            st_ctime=self.created,
                            st_mtime=self.created,
                            st_atime=self.created,
                            st_uid=65534, # nobody
                            st_gid=65534, # nobody
                            st_nlink=2)
            else:
                raise FuseOSError(errno.ENOENT)

    # TODO cache files back in local directory if remote
    def open(self, path, flags):
        log.debug("trying opening %s locally..." % path)
        try:
            return os.open(self.local + path, flags)
        except IOError:
            log.info("File %s doesn't exist locally..." % path)
            pass

        # now try downloading it

        filename = path[1:]
        if filename in self.central_files:
            log.debug("Downloading remote file %s" % path)
            # TODO try different peer if not succeeds
            peer = self.central_files[filename]["peers"][0]
            try:
                remote_file = requests.get("http://%s/%s" % (peer, filename))
            except requests.ConnectionError as e:
                log.error("File %s could not be downloaded from %s: %s" % (filename, peer, e))
                raise FuseOSError(errno.ENOENT)
            if remote_file.status_code is not 200:
                log.warn("File %s could not be downloaded from %s " % (filename, peer))
                raise FuseOSError(errno.ENOENT)
            else:
                log.info("downloaded %s from peer %s" % (filename, peer))
                # copy file to local dir
                log.debug("Writing file to %s" % (self.local + path))
                local_file = open(self.local + path, 'w')
                local_file.write(remote_file.content)
                local_file.close()
                log.debug("saved %s from peer %s" % (filename, peer))

                # now read it
                return os.open(self.local + path, flags)
        else:
            raise FuseOSError(errno.ENOENT)

    def read(self, path, size, offset, fh):
        # file handle is from os.open in `open`, so use it directly
        os.lseek(fh, offset, 0)
        return os.read(fh, size)

    def readdir(self, path, fh):
        log.debug("reading dir...")
        if (time.time() - self.last_fetched) > 5:
            log.info("central server file list is stale, refreshing...")
            self.central_files = self.get_central_files()
            self.last_fetched = time.time()
            log.info("Central server file list refreshed.")

        local_files = os.listdir(self.local + path)
        remote_files = \
            [f for f in self.central_files.keys() if f not in local_files]
        return ['.', '..'] + local_files + remote_files

    def release(self, path, fh):
        log.debug("Releasing file descriptor for %s" % path)
        # file handle is real, use it
        return os.close(fh)


# repeatedly refreshes server state while we're alive
def refresh(local_dir, central_server):
    local_files = os.listdir(local_dir)

    payload = {f: "fake hash" for f in local_files}
    hostname = socket.gethostname()

    j = json.dumps(dict(PEER="%s.mines.edu:6667" % hostname, files=payload))
    log.debug("sending payload to server: %s" % j)

    def process(res):
        if res.code is not 204:
            log.warn("Couldn't update central server! %s", res.code)
        else:
            log.info("Updated central server.")

    treq.post("http://%s/refresh" % central_server,
              data=j,
              headers={'Content-Type': ['application/json']}).addCallback(process)


if __name__ == "__main__":
    if len(argv) != 3:
        print('usage: %s <local directory> <mountpoint>' % argv[0])
        exit(1)

    local = argv[1]
    mountpoint = argv[2]

    # serve files from the local directory over HTTP
    # TODO subclass Site to add count of open connections to be able to
    # track "load" as defined by the project. Will also need to
    # do callFromThread from the FUSE stuff in order to track downloads.
    resource = File(realpath(local))
    factory = Site(resource)
    reactor.listenTCP(6666, factory)

    print "Starting twisted event loop..."

    # run reactor in separate thread, since FUSE is going to
    # block the main thread
    def start_loop():
        refresh(local, "localhost:6667")
        l = task.LoopingCall(refresh, local, "localhost:6667")
        l.start(5.0)
        reactor.run(False)

    t = threading.Thread(target=start_loop)
    t.start()

    print "Twisted loop started in separate thread."
    print "Now starting FUSE filesystem..."

    # run fuse main loop, this will block until unmounted or killed
    FUSE(NapsterFilesystem(local), mountpoint, foreground=True)

    print "FUSE received shutdown signal, shutting down reactor..."

    reactor.callFromThread(reactor.stop)

    print "bye!"
