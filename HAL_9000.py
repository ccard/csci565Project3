#! /usr/bin/env python

from flask import Flask
from flask import request
from flask import jsonify

import json
import sys

HAL_9000 = Flask(__name__)
cache = {}

@HAL_9000.route("/")
def query():
	q = request.args.get('q','')
	file_data = cache.get(q)
	if file_data is not None:
		return jsonify(file_data)

	return jsonify(cache)


@HAL_9000.route("/refresh",methods=['POST'])
def refresh():
	peer_data = request.get_json()
	peer_name = peer_data['PEER']
	peer_contents = peer_data['files']
	cache_dict = {}
	for f in peer_contents:
		cache_dict[f] = {'sha1' : peer_contents[f], 'peers' : [peer_name]}

	for f in cache_dict:
		if f in cache:
			file_data = cache[f]
			if file_data['sha1'] == cache_dict[f]['sha1']:
				if peer_name not in file_data['peers']:
					file_data['peers'].append(peer_name)

			cache[f] = file_data
		else:
			cache[f] = cache_dict[f]

	return '',204


if __name__ == "__main__":
	port = 6667
	if len(sys.argv) != 2:
		print "./HAL_9000.py [PORT]"
		exit()

	HAL_9000.run(host='0.0.0.0',port=port,debug=True)