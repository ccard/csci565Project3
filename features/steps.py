from lettuce import *
from subprocess import Popen, PIPE
import os
import sys
import re
import tempfile


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


@step('I can connect to the central server')
def can_I_connect(step):
    print "yes yes I can"


@step('Then I see that peers files')
def sea_files(step):
    print "i am getting sea sick"


@after.all
def cleanup(total):
    world.server.terminate()
