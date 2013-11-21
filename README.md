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
Our program requires severl python modules that are not installed on the school computers.  
To do this run command:
```
source environment
```

### Running the Peer Nodes and Tracking Server

#### Peer Node

#### Tracking Server
To start the tracking server run command `./HAL_9000.py [PORT] &`
to kill the tracking server run ps and kill the python task

## Testing
This section documents our user stories that we want to test as well as the results from our tests
### User Stories
- **Downloaders**:
 - Wishes to find a specified file on the system or find all the files that
  they can download from the system.
 - Would also like to download an uncorrupted version of the file.
 - Would like to be able to down load the file if the uploader is available.
 - Continue to run their client even if the tracking server or other 
   uploaders/downloaders are down.
- **Uploaders**:
 - Ensure that the tracking server eventually has the most recent snapshot of the files it is
  serving.
 - Ensure downloaders can still download even if the tracking server is down.
 - Continue running regardless of the state of the other uploaders/downloaders and the
  tracking server.

### Tests
The tests [features](features/find.feature) are defined in their own file 
using [lettuce](http://lettuce.it/). The tests are then implemented in the [steps](features/steps.py)
file.  To run the tests use the command `lettuce` in the parent directory and watch the magic happen.
