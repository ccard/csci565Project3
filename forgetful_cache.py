#! /usr/bin/env python

import datetime
import collections
import thread


class Forgetful_Cache:

    """docstring for Forgetful_Cache"""

    def __init__(self, timeout=5):
        self.lock = threading.Lock()
        self.timeout = timeout
        self.cache = collections.defaultdict

    def insert(self, key, value, peer):
        with self.lock:
            if key in self.cache:
                if (peer not in self.cache[key]['peers'] and
                   value['sha1'] == self.cache[key]['sha1']):
                    self.cache[key]['peers'].append(peer)

                threading.Timer(
                    self.timeout, self._purge, [key, peer])
            else:
                self.cache[key] = value
                threading.Timer(
                    self.timeout, self._purge, [key, peer])

    def _purge(self, key, peer):
        with self.lock:
            if key not in self.cache:
                return
            if len(self.cache[key]['peers']):
                if peer in self.cache[key]['peers']:
                    self.cache[key]['peers'].pop(
                        self.cache[key]['peers'].index(peer))
            else:
                self.cache.pop(key, None)

    def __getitem__(self, filekey):
        with self.lock:
            if filekey in self.cache:
                return self.cache[filekey].copy()
            else:
                return self.cache.copy()

    def __len__(self):
        with self.lock:
            return len(self.cache)
