#! /usr/bin/env python

import time
import collections
import threading


class ForgetfulCache:

    """ Timed cache that removes stale data
        after the initializing timeout has been reached. It uses system
        clocks to perfrom the time outs using the difference between the
        initializing time and the current time
    """

    def __init__(self, timeout=5):
        self.lock = threading.Lock()
        self.timeout = timeout
        self.cache = collections.defaultdict()
        self.timeout_log = {}

    def insert(self, filekey, value, peer):
        """ Add a file, associated peer and data to the cache

            Keyword arguments:
            filekey -- the name of the file
            value -- a dict containing its sha1 and the list of peers
                     its served from
            peer -- the peer that it is being served from
        """
        with self.lock:
            if filekey in self.cache:
                if (peer not in self.cache[filekey]['peers'] and
                   value['sha1'] == self.cache[filekey]['sha1']):
                    self.cache[filekey]['peers'].append(peer)
                self.timeout_log[filekey][peer] = time.time()
            else:
                self.cache[filekey] = value
                self.timeout_log[filekey] = {peer: time.time()}

    def _purge(self, filekey, peer):
        """ Purges the knowledge that a given file is served from a
            given peer if the file has no peers serving it it is
            removed from the cache

            Keyword arguments:
            filekey -- name of the file
            peer -- the peer node to be dereferenced from the file
        """
        if filekey not in self.cache:
            return
        print "Removing file's peer -> file: %s, peer: %s" % (filekey, peer)
        if len(self.cache[filekey]['peers']):
            if peer in self.cache[filekey]['peers']:
                self.cache[filekey]['peers'].pop(
                    self.cache[filekey]['peers'].index(peer))

        if not len(self.cache[filekey]['peers']):
            print "Deleting file-> file: %s, hash: %s" % (filekey, self.cache[filekey]['sha1'])
            self.cache.pop(filekey, None)

    def __getitem__(self, filekey):
        """ Redefines x[y] to use our desired functionality which is to search
            for the file in the cache and return the relavent data or return all the
            data in the cache if the file is not found

            Keyword arguments:
            filekey -- the file to search for
        """
        with self.lock:
            # First remove all stale data
            purging = {}
            for fkey in self.cache:
                purging[fkey] = []
                for peer in self.cache[fkey]['peers']:
                    currtime = time.time()
                    if ((currtime - self.timeout_log[fkey][peer]) >
                            self.timeout):
                        purging[fkey].append(peer)

            for fkey in purging:
                for peer in purging[fkey]:
                    self._purge(fkey, peer)

            # Search for file
            if filekey in self.cache:
                return self.cache[filekey].copy()
            else:
                return self.cache.copy()

    def __len__(self):
        with self.lock:
            return len(self.cache)
