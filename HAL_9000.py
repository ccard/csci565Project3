#! /usr/bin/env python

from flask import Flask
from flask import request
from flask import jsonify

from forgetful_cache import Forgetful_Cache

import json
import sys

HAL_9000 = Flask(__name__)
cache = Forgetful_Cache()


@HAL_9000.route("/")
def query():
    q = request.args.get('q', '')
    return jsonify(cache[q])


@HAL_9000.route("/refresh", methods=['POST'])
def refresh():
    peer_data = request.get_json()
    peer_name = peer_data['PEER']
    peer_contents = peer_data['files']
    cache_dict = {}
    for f in peer_contents:
        cache_dict[f] = {'sha1': peer_contents[f], 'peers': [peer_name]}

    for f in cache_dict:
        cache.insert(f, cache_dict[f], peer_name)

    return '', 204


if __name__ == "__main__":
    port = 6667
    if len(sys.argv) != 2:
        print "./HAL_9000.py [PORT]"
        exit()

    port = int(sys.argv[1])

    HAL_9000.run(host='0.0.0.0', port=port, debug=True)
