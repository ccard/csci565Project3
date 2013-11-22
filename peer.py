#! /usr/bin/env python
"""
Project 3 (NapsterFS) peer. Shares local files with
other peers as well as exposes remote files as a local
folder for download, using the central (HAL_9000) server
for discovery.

Usage:
  peer.py CENTRAL-SERVER LOCAL-PATH MOUNT-PATH [LOCAL-PORT]
  peer.py (-h | --help)

Arguments:
  CENTRAL-SERVER  Address of the central server as "hostname:port".
  LOCAL-PATH      Local directory of files to be shared. The directory
                  MUST NOT contain any subdirectories and MUST be
                  writable. Any remote files downloaded will be
                  written to this directory for availability after
                  the peer is closed.
  MOUNT-PATH      Empty directory to which the view of available files
                  will be mounted. The directory will be populated with
                  both locally-available files and remote files.
                  Accessing a remote file will result in that file
                  being downloaded and cached in the LOCAL-PATH.
  LOCAL-PORT      Unused port to which to bind. If not specified,
                  an OS-assigned ephemeral port is used.
                  Local files are shared to other peers over HTTP
                  on this port, so it must be accessible to other peers.

Options:
  -h --help     Show this screen.

"""
import hashlib
import logging
import os
import errno
import random
import socket
import time
import threading
import stat
import json
from os.path import realpath
from logging.config import dictConfig

from docopt import docopt
import requests
import treq
from twisted.internet import reactor, task
from twisted.web.static import File
from twisted.web.server import Site
from fuse import FUSE, FuseOSError, Operations, fuse_get_context
from twisted.application.service import Service


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


def byte_sha1(content):
    return hashlib.sha1(content).hexdigest()


#noinspection PyUnresolvedReferences
class NapsterFilesystem(Operations):
    """
    Essentially a union filesystem between a local directory and the
    central server.

    The files shown in this FUSE-mounted directory are the union of local files
    and peer-hosted files.  When a non-local file is downloaded, it's cached in
    the local directory for future reads, as well as becoming shared from this
    host.

    File writes are unsupported, though any changes to the local directory will
    be reflected in this directory.
    """

    def __init__(self, l_dir, central):
        self.local = realpath(l_dir)

        self.created = time.time()
        self.central_server = central

        self.central_files = self.get_central_files()
        self.last_fetched = time.time()

    def get_central_files(self):
        """
        Returns the set of all files available on the server, possibly including
        our own files. The JSON response is parsed as a dict.
        """
        try:
            files = requests.get('http://%s/' % self.central_server)
        except requests.ConnectionError as c_err:
            log.error("Couldn't get files from central server: %s" % c_err)
            return {}
        if files.status_code is not 200:
            log.error("Couldn't get files from central server: %s" % files)
            return {}
        else:
            files = files.json()
            log.info("Received files from central server: %s", files)
            return files

    #noinspection PyMethodOverriding
    def getattr(self, path, fd):
        """
        Returns the file attributes for a given path, i.e. file type, permissions,
        etc. If the requested file is remote, we assume that it's owned by
        nobody, to avoid having to download all the files when a directory is listed.
        Instead, the actual download is performed on read.
        """
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
                st = os.lstat(self.local + path)  # read attrs locally
                d = dict((key, getattr(st, key)) for key in ('st_atime',
                                                             'st_ctime',
                                                             'st_gid',
                                                             'st_mode',
                                                             'st_mtime',
                                                             'st_nlink',
                                                             'st_size',
                                                             'st_uid'))
                d["st_mode"] = (stat.S_IFREG | 0o444)  # set as readonly
                return d
            except OSError:
                log.info("File %s doesn't exist locally..." % path)

                filename = path[1:]
                if filename in self.central_files:
                    log.debug("File %s exists on central server...", filename)
                    return dict(st_mode=(stat.S_IFREG | 0o444),
                                st_ctime=self.created,
                                st_mtime=self.created,
                                st_atime=self.created,
                                # nobody
                                st_uid=65534,
                                st_gid=65534,
                                st_nlink=2)
                else:
                    raise FuseOSError(errno.ENOENT)

    def open(self, path, flags):
        """
        Returns a file handle to the file at `path`.
        For locally available files, proxy to os.open.
        For remote files, download and cache the remote file before
        opening the now-cached version with os.open.
        """
        log.debug("trying opening %s locally..." % path)
        try:
            return os.open(self.local + path, flags)
        except OSError:
            log.info("File %s doesn't exist locally..." % path)
            pass

        # now try downloading it

        filename = path[1:]
        if filename in self.central_files:
            log.debug("Downloading remote file %s" % path)

            # choose a peer, taking into account load and latency,
            # then quickly discarding load and latency in favor of
            # a random choice. there aren't any requirements on
            # performance anyway, so choosing based on
            # latency/load is overkill
            peers = self.central_files[filename]["peers"]
            peer = random.choice(peers)

            sha = self.central_files[filename]["sha1"]
            try:
                remote_file = requests.get("http://%s/%s" % (peer, filename))

                received_sha = byte_sha1(remote_file.content)
            except requests.ConnectionError as c_err:
                log.error("File %s could not be downloaded from %s: %s" % (filename, peer, c_err))
                raise FuseOSError(errno.ENOENT)

            if remote_file.status_code is not 200:
                log.error("File %s could not be downloaded from %s " % (filename, peer))
                raise FuseOSError(errno.ENOENT)
            elif received_sha != sha:
                log.error("File %s downloaded from %s doesn't match hash %s (got %s)!" %
                          (filename, peer, sha, received_sha))
                raise FuseOSError(errno.ENOENT)
            else:
                log.info("downloaded %s from peer %s" % (filename, peer))
                # copy file to local dir
                log.debug("Writing file to %s" % (self.local + path))
                
                try:
                    with open(self.local + path, 'w') as local_file:
                       local_file.write(remote_file.content)
                       local_file.flush()
                       os.fsync(local_file)

                    with open(self.local + path, 'r') as local_file:
                       c = local_file.read()
                       assert c == remote_file.content

                       log.debug("written %s from peer %s" % (filename, peer))

                except Exception, e:
                    log.error(e)
                

                log.debug("sleeping, %s from peer %s" % (filename, peer))
                # In this system, each peer has a fake latency between
                # 100ms-5000ms, which just so happens to be 1000ms for all peers.
                time.sleep(1)
                # XXX also, for some reason, the tests can't read the contents
                # of file we just wrote _unless_ we sleep here for 1 second (on
                # some machines). This is bizarre, we don't understand it.

                log.debug("saved %s from peer %s" % (filename, peer))

                # now read it
                return os.open(self.local + path, flags)
        else:
            raise FuseOSError(errno.ENOENT)

    def readdir(self, path, fh):
        """
        list files in the directory. Since we're doing a union mount,
        we hit the central server (or use a cached version) to return the union
        of centrally available files and our local files.
        """
        log.debug("reading dir...")
        if (time.time() - self.last_fetched) > 5:
            log.info("central server file list is stale, refreshing...")
            self.central_files = self.get_central_files()
            self.last_fetched = time.time()
            log.info("Central server file list refreshed.")

        local_files = os.listdir(self.local + path)
        remote_files = \
            [f for f in self.central_files.keys() if f not in local_files]
        log.debug(remote_files)
        return ['.', '..'] + local_files + remote_files

    def read(self, path, size, offset, fh):
        """
        Read bytes from a file handle.
        File handle is from os.open in `open` i.e. is a real file handle,
        so use it directly.
        """
        os.lseek(fh, offset, 0)
        return os.read(fh, size)

    def release(self, path, fh):
        """
        Release an open file handle.
        File handle is from os.open in `open` i.e. is a real file handle,
        so close it directly.
        """
        return os.close(fh)


def sha1(path):
    with open(path, "rb") as f:
        return hashlib.sha1(f.read()).hexdigest()


# repeatedly refreshes server state while we're alive
def refresh(l_dir, central, port):
    local_files = os.listdir(l_dir)

    payload = {f: sha1(l_dir + "/" + f) for f in local_files}
    peer_addr = "%s:%s" % (socket.getfqdn(), port)

    j = json.dumps(dict(PEER=peer_addr, files=payload))
    log.debug("sending payload to server: %s" % j)

    def process(res):
        if res.code is not 204:
            log.error("Couldn't update central server! %s", res.code)
        else:
            log.info("Updated central server.")

    post = treq.post("http://%s/refresh" % central,
                     data=j,
                     headers={'Content-Type': ['application/json']},
                     timeout=4)
    post.addCallback(process)
    post.addErrback(log.error)


if __name__ == "__main__":
    args = docopt(__doc__)
    central_server = args['CENTRAL-SERVER']
    local_dir = args['LOCAL-PATH']
    mount_point = args['MOUNT-PATH']
    local_port = args['LOCAL-PORT']
    if local_port is None:
        local_port = 0

    # serve files from the local directory over HTTP
    resource = File(realpath(local_dir))
    factory = Site(resource)
    port = reactor.listenTCP(int(local_port), factory)

    # if binding to port 0, get actual listening port that OS assigned us
    local_port = port.getHost().port

    print "Starting twisted event loop, listening on %s..." % local_port

    # run reactor in separate thread, since FUSE is going to
    # block the main thread
    def start_loop():

        # start server polling
        l = task.LoopingCall(refresh, local_dir, central_server, local_port)
        l.start(5.0)

        # don't try to install signal handlers, since separate threads can't do so
        reactor.run(installSignalHandlers=0)

    t = threading.Thread(target=start_loop)
    t.start()

    print "Twisted loop started in separate thread."
    print "Now starting FUSE filesystem..."

    # run fuse main loop, this will block until unmounted or killed
    try:
        FUSE(NapsterFilesystem(local_dir, central_server), mount_point, foreground=True)
        print "FUSE received shutdown signal, shutting down reactor..."
    except Exception as e:
        print "Something went wrong with fuse!"

    reactor.callFromThread(reactor.stop)

    print "bye!"
