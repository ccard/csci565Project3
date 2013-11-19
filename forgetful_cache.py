#! /usr/bin/env python

import time
import collections
import threading


class Forgetful_Cache:

    """docstring for Forgetful_Cache"""

    def __init__(self, timeout=10):
        self.lock = threading.Lock()
        self.timeout = timeout
        self.cache = collections.defaultdict()
        self.timeout_log = {}

    def insert(self, filekey, value, peer):
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
            if filekey not in self.cache:
                return
            print "removing file:: file: %s, key %s" % (filekey, peer)
            if len(self.cache[filekey]['peers']):
                if peer in self.cache[filekey]['peers']:
                    self.cache[filekey]['peers'].pop(
                        self.cache[filekey]['peers'].index(peer))

            if not len(self.cache[filekey]['peers']):
                self.cache.pop(filekey, None)

    def __getitem__(self, filekey):
        with self.lock:
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

            if filekey in self.cache:
                return self.cache[filekey].copy()
            else:
                return self.cache.copy()

    def __len__(self):
        with self.lock:
            return len(self.cache)
