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

    def insert(self, key, value):
        with self.lock:
            if key in self.cache:
                self.cache[key]['status_counter'] += 1
                threading.Timer(self.timeout, self.purge, [key])
            else:
                value['status_counter'] = 0
                self.cache[key] = value
                threading.Timer(self.timeout, self.purge, [key])

    def purge(self, key):
        with self.lock:
            if key not in self.cache:
                return
            if self.cache[key]['status_counter'] > 0:
                self.cache[key]['status_counter'] -= 1
            else:
                self.cache.pop(key, None)

    def __getitem__(self, filekey):
        with self.lock:
            if filekey in self.cache:
                value = self.cache[key].copy()
                value.pop('status_counter', None)
                return value
            else:
                retCache = self.cache.copy()
                for f in retCache:
                    retCache[f].pop('status_counter', None)
                return retCache

    def __len__(self):
        with self.lock:
            return len(self.cache)
