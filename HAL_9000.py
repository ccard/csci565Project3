#! /usr/bin/env python

from flask import Flask
from flask import request
from werkzeug.contrib.cache import SimpleCache

import json
import sys

HAL_9000 = Flask(__name__)
cache = SimpleCache()

@HAL_9000.route("/")
def query():
	q = request.args.get('q','')
	file_data = cache.get(q)
	if file_data is not None:
		return file_data

	return 404


@HAL_9000.route("/refresh",methods=['POST'])
def refresh():
	peer_data = request.get_json()
	peer_name = peer_data['PEER']
	peer_contents = peer_data['files']
	cache_dict = {}
	for f in peer_contents:
		cache_dict[f] = {'sha1' : peer_contents[f], 'peers' : [peer_name]}

	for f in cache_dict:
		if cache.get(f) is not None:
			file_data = json.loads(cache.get(f))
			if file_data['sha1'] == cache_dict[f]['sha1']:
				if peer_name not in file_data['peers']:
					file_data['peers'].append(peer_name)

			cache.set(f,json.dumps(file_data),5)
		else:
			cache.set(f,json.dumps(cache_dict[f]),5)

	return 204


if __name__ == "__main__":
	port = 6667
	if len(sys.argv) != 2:
		print "./HAL_9000.py [PORT]"
		exit()

	HAL_9000.run(port=port)