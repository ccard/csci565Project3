#! /bin/bash

socat UDP4-DATAGRAM:224.1.0.1:6666\
,bind=:6666,range=138.67.0.0/16,\
ip-add-membership=224.1.0.1:0,reuseaddr,\
ip-multicast-loop=false EXEC:./echo_script.sh