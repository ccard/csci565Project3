from lettuce import *
from subprocess import Popen, PIPE
import os
import sys
import re
import tempfile
import time
import requests


@step('running central server')
def running_central_server(step):
    world.server = Popen(['./HAL_9000.py', '6667'], stderr=PIPE)
    output = world.server.stderr.readline()
    assert re.search("\*\sRunning on.*", output) is not None


@step('peer hosting files')
def peer_hosting_files(step):
    world.mount_point = tempfile.mkdtemp()
    world.local_dir = tempfile.mkdtemp()

    for i in range(1, 5):
        open(world.local_dir + "/f" + repr(i) + ".txt", 'a').close()

    world.peer_uploader = Popen(
        ['./peer.py', 'localhost:6667',
            world.local_dir, world.mount_point, '6666'],
        stderr=PIPE, stdout=PIPE)

    time.sleep(3)


@step('I can connect to the central server')
def can_I_connect(step):
    r = requests.head("http://localhost:6667")
    assert r.status_code == 200


@step('Then I see that peers files')
def sea_files(step):
    r = requests.get("http://localhost:6667")
    r = r.json()
    for f in range(1, 5):
        fname = "f%s.txt" % repr(f)
        assert fname in r


@after.all
def cleanup(total):
    print "server %d" % world.server.pid
    world.server.terminate()
    world.server.wait()
    print "peer %d" % world.server.pid
    world.peer_uploader.terminate()
    world.peer_uploader.wait()
