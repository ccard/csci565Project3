csci565Project3
===============

**Authors: Chris Card, Steven Ruppert**

## Files

- `HAL_9000.py`: a Flask-based python HTTP web server that functions
  as the tracking server for our distributed file system.

- `peer.py`: one of the peers operating in the distributed file system. It
  functions as the user interface as well as a peer node.  It is responsible
  for keeping the tracking server up to date with the files it has and can
  serve. It is also responsible for querying for files as well as downloading
  the files.

- `requirements.txt`: contains all the modules that our program requires to
  run for use with `pip`.

- `features/sharing.feature`: defines our tests in the human readable
  Gherkin format.

- `features/steps.py`: implements the tests defined in the `.feature` file
  using lettuce, which allows us to create easy to understand and highlighted
  test output.

## Design

Our distributed file system is comprised of two parts:

1. Tracking Server
2. Peer Node

### Tracking Server

The Tracking server is responsible for knowing the currently available files in
the system and serving query requests from peer nodes in about the files in the
system.  It is designed to be a state-full server but does not persist its
knowledge of the files in the system, through the use of a timed cache.  By
using a timed cache the tracking server tolerates peer node failures by simply
timing out the files associated with the peer, if the peer does not refresh the
tracking server within a given time interval.  The tracking server itself is
tolerant to its own failures because it's state is stored in memory.  So it only
has to wait for the peer nodes to connect and refresh it when it
starts/restarts.

### Peer Node

The peer nodes in our system are broken into two types downloaders and
uploaders. Each peer is both an uploader and a downloader this paradigm helps
us to define the responsibilities of a peer and what kind of faults the peer is
tolerant of.

The peer's responsibility as an *uploader* is to ensure that the tracking
server eventually knows about all files that it is willing to upload.  This is
done by periodically (about every 5 *sec*) resending all files it is willing to
upload to the tracking server, other wise the tracking server will simply
forget about it.  Its other responsibility is to ensure it can upload all files
that it told the tracking server about unless it experiences a fault within
5 *sec* of telling the tracking server of the files its willing to upload.  The
uploader must be tolerant to faults in the tracking server as well as other
peers.  It is tolerant to faults in the tracking server by continuing to run
and periodically trying to reconnect with the tracking server.  It is tolerant
to faults in other peers because it is only waiting for inbound tcp connections
from other peers.  It is tolerant to faults within itself because it only
serves files out of a dedicated directory.

The peer's responsibility as a *downloader* is to be able to find all or
desired files in the system, be able to download an uncorrupted version of the
file and be able to download the file so long as one peer that is serving file
is still running.  The only fault that the downloader is not tolerant to is
the tracking server either failing before or while processing the downloaders
query.  Once the tracking server returns the result of the query the downloader
no longer cares if the tracking server is running or not.  Its able to download
all files that the tracking server told it about so long as the peers willing
to upload them are running.  The downloader is tolerant of corrupted files
because it hashes the received file with *sha1* and compares it with the
expected hash it got from the tracking server.  If the hashes are not the same
it goes to another node that is willing to upload the file, so long as one
uploading peer has an uncorrupted version of the file it will find it.  The
downloader is tolerant to faults in other peers, it will continue to run
regardless of the state of other peers.

## Execution

### Environment Setup

Our program requires several python modules that are not installed on the
school computers.  To setup the environment run:

    source environment

### Running the Peer Nodes and Tracking Server

#### Peer Node

##### A Little Bit of Setup

To setup the MOUNT-DIR create a new directory in `/tmp/<your dir name>`
replacing `<your dir name>` with a unique name.
The MOUNT-DIR you just created will be used as the mounting point when starting
the peer node below. The LOCAL-DIR is the
path to the directory of files that you wish your peer to notify the tracking
server that it is willing to upload.
This can be an existing directory or it can be one that you create your self.

##### Using the Peer Node

To start the peer node:

    ./peer.py CENTRAL-SERVER LOCAL-PATH MOUNT-PATH`

Where `CENTRAL-SERVER` is the address and port of the central server,
`LOCAL-PATH` is a directory containing files you wish to share and
`MOUNT-PATH` is an available empty directory.

After starting the client, `MOUNT-PATH` is populated with a view of all files
available throughout the network--both your own files and remote files. Local
files can be opened and read just as the original files can. Remote files
appear in the directory listing, but are not downloaded until read time, at
which the remote file is downloaded to `LOCAL-PATH` so it can be read as well
as re-shared with the rest of the network.

To avoid flooding the network, the peer only checks for new files on the server
every 5 seconds, and sends its own local file list every 5 seconds.
If the peer cannot reach the central server, it will log a failure and continue
to work with the files it has available.

Note that if the mounted directory is viewed in a GUI viewer such as
`nautilus`, new files won't be seen until after a manual refresh (CTRL + R).
Furthermore, nautilus may choose to read file contents, triggering a mass
download when the directory is opened. Using shell commands such as `ls` and
`cat` may provide more deterministic behavior.

#### Tracking Server

To start the tracking server:

    ./HAL_9000.py [PORT]

## Testing

### User Stories

- **Downloaders**:
  - Wishes to find a specified file on the system or find all the files that
    they can download from the system.
  - Would also like to download an uncorrupted version of the file.
  - Would like to be able to down load the file if the uploader is
    available.
  - Continue to run their client even if the tracking server or other
    uploaders/downloaders are down.
- **Uploaders**:
  - Ensure that the tracking server eventually has the most recent snapshot of
    the files it is serving.
  - Continue running regardless of the state of the other uploaders/downloaders
    and the tracking server.

### Tests

The tests [features](features) are defined BDD-style in their own file using
[lettuce](http://lettuce.it/). The tests are then implemented in the
[steps](features/steps.py) file. To run the tests use the command `lettuce` in
the parent directory and watch the magic happen.
