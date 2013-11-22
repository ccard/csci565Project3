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

- `features/find.feature`: This file defines our tests in a human readable format that is then parsed
 `steps.py` when the command `lettuce` is run in the parent directory.

- `features/steps.py`: This file implements the tests defined in `find.features` and hooks each test
 method to one of the lines in `find.features`.  Using lettuce allows us to create easy to understand
 and highlighted test output  

## Design

Our distrubuted file system is comprised of two parts:

1. Tracking Server
2. Peer Node

### Tracking Server

The Tracking server is responsible for knowing what files are in the system and serving query requests from 
peer nodes.

### Peer Node

## Execution

### Environment Setup
Our program requires severl python modules that are not installed on the school computers.  
To do this run command:
```
source environment
```

### Running the Peer Nodes and Tracking Server

#### Peer Node

##### A Little bit of Setup

To setup the MOUNT-DIR create a new directory in `/tmp/<your dir name>` replacing `<your dir name>` with a unique name.
The MOUNT-DIR you just created will be used as the mounting point when starting the peer node below. The LOCAL-DIR is the
path to the directory of files that you wish your peer to notifiy the tracking server that it is willing to upload them.
This can be an exisitng directory or it can be one that you create your self.

##### Using the Peer Node

To start the peer node run command `./peer.py CENTRAL-SERVER LOCAL-PATH MOUNT-PATH LOCAL-PORT`. To get more
details on what the different parameters are run `./peer.py [-h | --help]`. The MOUNT-PATH now contains all files
that other peers in this system are willing to upload to find. To find the files in the system use `ls MOUNT-DIR`.
When you want to download a specific file just perform any file system operation that reads the file.
For example `cat <the file name>`, `less <the file name>` or even `vim <the file name>`.


#### Tracking Server

To start the tracking server run command `./HAL_9000.py [PORT] &`
to kill the tracking server run ps and kill the python task.

## Testing

This section documents our user stories that we want to test.

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
