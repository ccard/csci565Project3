from lettuce import *
from subprocess import Popen, PIPE
import os
import sys
import re
import tempfile
import time
import requests


@before.each_scenario
def setup(scenario):
    world.peers = {}


@step('running central server')
def running_central_server(step):
    world.server = Popen(['./HAL_9000.py', '6667'], stderr=PIPE)
    output = world.server.stderr.readline()
    assert re.search("\*\sRunning on.*", output) is not None


def run_peer(name, files=None):
    if not files:
        files = {}
    mount_point = tempfile.mkdtemp()
    local_dir = tempfile.mkdtemp()
    state = dict(mount_point=mount_point, local_dir=local_dir, files=files)

    for filename, contents in files.items():
        f = open("%s/%s" % (local_dir, filename), 'w')
        f.write(contents)
        f.close()

    state["process"] = Popen(
        ['./peer.py', 'localhost:6667',
         local_dir, mount_point, '0'],
        stderr=PIPE, stdout=PIPE)

    # wait for process to spin up
    time.sleep(2)

    world.peers[name] = state


@step('another peer hosting files')
def peer_hosting_files(step):
    run_peer("remote", files=dict(f1="hello", f2="world"))


@step('I launch my own peer')
def launch_own_peer(step):
    run_peer("me")


@step('Then I see that peer\'s files')
def see_files(step):
    contents = os.listdir(world.peers['me']['mount_point'])
    assert "f1" in contents, "f1 not found in mount point: %s" % contents
    assert "f2" in contents, "f2 not found in mount point: %s" % contents


@step('I can download and read the remote file')
def open_file(step):
    mount_point = world.peers['me']['mount_point']
    ls = os.listdir(world.peers['me']['mount_point'])
    try:
        with open(mount_point + "/f1", 'r') as f:
            contents = f.read()
            assert contents == "hello", \
                   "actual contents: %s, ls: %s " % (contents, ls)
    except IOError:
        assert False, "couldn't read file f1!"


@step('I launch a peer sharing a file')
def add_file(step):
    run_peer("me", files={"my-file": "sup dawg"})


@step('another peer connects|a connected peer')
def connect_another_peer(step):
    run_peer("remote", files={})


@step('they can download and read my file')
def check_remote(step):
    mount_point = world.peers['remote']['mount_point']
    ls = os.listdir(world.peers['remote']['mount_point'])
    try:
        with open(mount_point + "/my-file", 'r') as f:
            contents = f.read()
            assert contents == "sup dawg", \
                   "actual contents: %s, ls: %s " % (contents, ls)
    except IOError:
        assert False, "couldn't read my-file from remote, available: %s" % ls


@step('the server goes down')
def kill_server(step):
    world.server.terminate()
    world.server.wait()


@step('the (?:other peer|peer) goes down')
def kill_other_peer(step):
    kill_peer(world.peers["remote"])


def kill_peer(peer):
    peer["process"].terminate()
    peer["process"].wait()
    for filename in peer["files"].keys():
        try:
            os.remove(peer["local_dir"] + "/" + filename)
        except:
            pass
    try:
        os.rmdir(peer["local_dir"])
    except:
        pass
    try:
        os.rmdir(peer["mount_point"])
    except:
        pass

@step('the server is still running')
def check_server(step):
    assert world.server.poll() is None, 'Server is dead!'

@step('my peer is still running')
def check_server(step):
    assert world.peers["me"]["process"].poll() is None, \
           'My peer is dead!'

@after.each_scenario
def cleanup(scenario):
    if world.server.poll() is None:
        world.server.terminate()
        world.server.wait()

    for peer in world.peers.values():
        if peer["process"].poll() is None:
            kill_peer(peer)

