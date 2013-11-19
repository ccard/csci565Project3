#! /usr/bin/env python
import hashlib
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


def byte_sha1(content):
    return hashlib.sha1(content).hexdigest()


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

    def __init__(self, dir, central):
        self.local = realpath(dir)

        self.created = time.time()
        self.central_server = central

        self.central_files = self.get_central_files()
        self.last_fetched = time.time()

        # upload file list to refresh master server
        self.refresh_files()
        self.last_refreshed = time.time()

    def refresh_files(self):
        local_files = os.listdir(self.local)
        payload = {f: "fake hash" for f in local_files}
        hostname = socket.gethostname()
        j = json.dumps(dict(PEER="%s.mines.edu:6667" % hostname, files=payload))
        debug("sending payload to server: %s" % j)
        res = requests.post("http://%s/refresh" % self.central_server, data=j, headers={
            'Content-Type': 'application/json'
        })
        if res is not 200:
            warn("Couldn't update central server! %s", res)
        else:
            info("Updated central server")
        pass

    def get_central_files(self):
        """
        Returns the set of all files available on the server, possibly including
        our own files. The JSON response is parsed as a dict.
        """
        try:
            files = requests.get('http://%s/' % self.central_server)
        except requests.ConnectionError as e:
            log.error("Couldn't get files from central server: %s" % e)
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
            except IOError:
                log.info("File %s doesn't exist locally..." % path)

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

            # TODO download remote if exists
            filename = path[1:]
            if filename in self.central_files:
                debug("File %s exists on central server...", filename)
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
        """
        Returns a file handle to the file at `path`.
        For locally available files, proxy to os.open.
        For remote files, download and cache the remote file before
        opening the now-cached version with os.open.
        """
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
            sha = self.central_files[filename]["sha1"]
            try:
                remote_file = requests.get("http://%s/%s" % (peer, filename))
                received_sha = byte_sha1(remote_file.content)
            except requests.ConnectionError as e:
                log.error("File %s could not be downloaded from %s: %s" % (filename, peer, e))
                raise FuseOSError(errno.ENOENT)

            if remote_file.status_code is not 200:
                log.error("File %s could not be downloaded from %s " % (filename, peer))
                raise FuseOSError(errno.ENOENT)
            elif received_sha is not sha:
                log.error("File %s downloaded from %s doesn't match hash %s (got %s)!" %
                          (filename, peer, sha, received_sha))
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
def refresh(dir, central, port):
    local_files = os.listdir(dir)

    payload = {f: sha1(dir + "/" + f) for f in local_files}
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
    if len(argv) != 5:
        print('usage: %s <central server> <local directory> <mountpoint> <local port>' % argv[0])
        exit(1)

    _, central_server, local_dir, mount_point, local_port = argv

    # serve files from the local directory over HTTP
    # TODO subclass Site to add count of open connections to be able to
    # track "load" as defined by the project. Will also need to
    # do callFromThread from the FUSE stuff in order to track downloads.
    resource = File(realpath(local_dir))
    factory = Site(resource)
    reactor.listenTCP(int(local_port), factory)

    print "Starting twisted event loop..."

    # run reactor in separate thread, since FUSE is going to
    # block the main thread
    def start_loop():
        l = task.LoopingCall(refresh, local_dir, central_server, local_port)
        l.start(5.0)
        reactor.run(installSignalHandlers=0)

    t = threading.Thread(target=start_loop)
    t.start()

    print "Twisted loop started in separate thread."
    print "Now starting FUSE filesystem..."

    # run fuse main loop, this will block until unmounted or killed
    FUSE(NapsterFilesystem(local_dir, central_server), mount_point, foreground=True)

    print "FUSE received shutdown signal, shutting down reactor..."

    reactor.callFromThread(reactor.stop)

    print "bye!"
