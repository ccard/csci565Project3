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

Our distributed file system is comprised of two parts:

1. Tracking Server
2. Peer Node

### Tracking Server

The Tracking server is responsible for knowing the currently available files in the system and serving query 
requests from peer nodes in about the files in the system.  It is designed to be a state-full server but does
not persist its knowledge of the files in the system, through the use of a timed cache.  By using a timed cache
the tracking server tolerates peer node failures by simply timing out the files associated with the peer, if the
peer does not refresh the tracking server within a given time interval.  The tracking server it self is tolerent
to its own failures because its state is stored in memory.  So it only has to wait for the peer nodes to connect 
and refresh it when it starts/restarts.

### Peer Node

The peer nodes in our system are broken into two types downloaders and uploaders. Each peer is both an uploader 
and a downloader this paradigm helps us to define the responsibilities of a peer and what kind of faults the peer 
is tollerent of.

The peer's responsibility as an *uploader* is to ensure that the tracking server eventually knows
about all files that it is willing to upload.  This is done by periodically (about every 5 *sec*) resending all 
files it is willing to upload to the tracking server, other wise the tracking server will simply forget about 
it. Its other responsibility is to ensure it can upload all files that it told the tracking server about unless 
it experiences a fault within 5 *sec* of telling the tracking server of the files its willing to upload. 
The uploader must be tollerent to faults in the tracking server as well as other peers.  It is tollerent to
faults in the tracking server by continuing to run and periodically trying to reconnect with the tracking server. 
It is tollerent to faults in other peers because it is only waiting for inbound tcp connections from other peers. 
It is tollerent to faults within itself because it only servs files out of a dedicated directory.

The peer's responsibility as a *downloader* is to be able to find all or desired files in the system, be able to 
download an uncorreupted version of the file and be able to download the file so long as one peer that is serving 
file is still running.  The only fault that the downloader is not tollerent to is the tracking server either failing 
before or while proccessing the downloaders query.  Once the tracking server returns the result of the query 
the downloader no longer cares if the tracking server is running or not.  It able to download all files that 
the tracking server told it about so long as the peers willing to upload them are running.  The downloader 
it tollerent of corrupted files because it hashes the recieved file with *sha1* and compares it with the expected 
hash it got from the tracking server.  If the hashse are not the same it goes to another node that is willing to 
upload the file, so long as one uploading peer has an uncorrupted version of the file it will find it.  The 
downloader is tolent to faults in other peers, it will continue to run regardless of the state of other peers. 


## Execution

### Environment Setup
Our program requires several python modules that are not installed on the school computers.  
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
 - Continue running regardless of the state of the other uploaders/downloaders and the
  tracking server.

### Tests

The tests [features](features/find.feature) are defined in their own file 
using [lettuce](http://lettuce.it/). The tests are then implemented in the [steps](features/steps.py)
file.  To run the tests use the command `lettuce` in the parent directory and watch the magic happen.
