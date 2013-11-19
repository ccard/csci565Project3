#! /usr/bin/env python

import datetime
import collections
import thread

class Forgetful_Cache:
	"""docstring for Forgetful_Cache"""
	def __init__(self, timout=5):
		self.lock = threading.Lock()
		 
