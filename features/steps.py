from lettuce import *


@step('running central server')
def running_central_server(step):
    print "The server is running"


@step('peer hosting files')
def peer_hosting_files(step):
    print "Hosting"


@step('I can connect to the central server')
def can_I_connect(step):
    print "yes yes I can"


@step('Then I see that peers files')
def sea_files(self):
    print "i am getting sea sick"
