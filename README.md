csci565Project3
===============

**Authors: Chris Card, Steven Ruppert**

## Files
- `HAL_9000.py`: This file contains the python http web server that functions as the tracking server for our distrubuted file system

- `peer.py`: This file represents one of the peers on
operating in the distrubited file system. It functions 
as the user interface as well as a peer node.  It is responsible for keeping the tracking server up to date
with the files it has and can serve. It is also reponsible
for quering for files as well as downloading the files.

- `latencies.yaml`: This file defines the latencies between
different servers in our network in seconds.

- `requirements.txt`: This fill contains all the modules
that our program requires to run.

## Design

## Execution

### Environment Setup
Our program requires severl python modules that are not installed on the school computers.  To do this run command:
```
source environment
```

### Running the Peer Nodes and Tracking Server

#### Peer Node

#### Tracking Server
To start the tracking server run command `./HAL_9000.py [PORT] &`
to kill the tracking server run ps and kill the python task