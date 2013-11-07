#! /bin/bash

socat STDIO UDP4-DATAGRAM:224.1.0.1:6666,\
bind=:6666,range=138.67.0.0/16,\
ip-add-membership=224.1.0.1:138.67.186.225,\
reuseaddr,ip-multicast-loop=false