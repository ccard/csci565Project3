#! /usr/bin/env python

import datetime
import collections
import threading


class Forgetful_Cache:

    """docstring for Forgetful_Cache"""

    def __init__(self, timeout=5):
        self.lock = threading.Lock()
        self.timeout = timeout
        self.cache = collections.defaultdict()

    def insert(self, filekey, value, peer):
        with self.lock:
            if filekey in self.cache:
                if (peer not in self.cache[filekey]['peers'] and
                   value['sha1'] == self.cache[filekey]['sha1']):
                    self.cache[filekey]['peers'].append(peer)

                timer = threading.Timer(
                    self.timeout, self._purge, [filekey, peer])
                timer.start()
            else:
                self.cache[filekey] = value
                threading.Timer(
                    self.timeout, self._purge, [filekey, peer])
                timer.start()

    def _purge(self, filekey, peer):
        with self.lock:
            print "Attempting removal:: file: %s , peer: %s" % (filekey, peer)
            if filekey not in self.cache:
                return
            if len(self.cache[filekey]['peers']):
                if peer in self.cache[filekey]['peers']:
                    print "removing peer"
                    self.cache[filekey]['peers'].pop(
                        self.cache[filekey]['peers'].index(peer))
            else:
                print "removing file"
                self.cache.pop(filekey, None)

    def __getitem__(self, filekey):
        with self.lock:
            if filekey in self.cache:
                return self.cache[filekey].copy()
            else:
                return self.cache.copy()

    def __len__(self):
        with self.lock:
            return len(self.cache)
