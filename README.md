# Building a simple P2P chat network
### _aka playing with sockets and threads in Python_

This project is the result of some of my explorations on the idea of "backend" work while at the [Recurse center](www.recurse.com). I started this with some knowledge on P2P networks from undergrad networking classes, but have never actually done any implementation.

## Approach
I started this project by reading this [writeup and code of a P2P framework](http://cs.berry.edu/~nhamid/p2p/). I liked how she conceptually divided the various pieces in her and have adopted some of it in my implementation. 

I also used pytest to test some of the functionality, though am not sure if this is the right way to do it.

## Components

### [Peer](peer.py)
I started with the idea of a Peer, where a Peer's responsibility is to manage the overall operations of the network. That is, it should listen for incoming connections and create separate threads to handle the connections. It should also allow the user to maintain a list of known peers optionally. 

#### Initialization
A Peer is initialized with:
* `id`: a name for instance, or a uuid
* `port`: a number for the port it should listen on
* `host`: host name of the server
* `debug (defaults = False)`: boolean value to print debug messages
* `autostart (default = True)`: boolean value to immediately bind socket and start listening. If set to False, listening will only start when `start_listening()` is called.

#### Usage
**Start server port and listening**

execute `start_listening()` to listen on user-defined serverport if not autostart. This will create a listening thread that will handle incoming connections

**Message Format**

Messages between peers are sent and received in the following JSON format:
```
{
	'msg_type': <msgtype>, # pre-defined msgtype
	'msg': <msg>, # message payload
    'originator': <originator>, #peer id of originator
    'time': time # time msg was sent
}
```
When the peer handles messages, the data for each of these JSON fields are used as parameters for the handling functions. Thus, handler functions must have the following parameters, even though they might not be used in the function:
* msg_type
* msg
* originator
* time

**Adding Handlers**

To use a Peer, the programmer can register handlers for specific message types such that the listening loop can dispatch incoming requests to these handlers according to the type of message received. For instance:

```
handlers = {"TEST": handle_test, 
			"PING": handle_ping}
for h in handlers:
	self.add_handler(h, handlers[h])
```
Thus, when a message with the "TEST" message type is received, the function handle_test() will be called.

If an unknown message type is received, Peer does nothing with the message. A statement will be printed if debug mode is on

**Maintaining List of Peers**
Three methods `get_peers()`, `add_peers()` and `find_peers()` can be used to maintain, add and find a peer from a node's list of peers.

#### Shutdown
`shutdown()` should be called at the end of the program to properly shutdown sockets and threads that are alive

---
### [Peer Connection](peerconnection.py)
This module encapsulates the creation, use and shutdown of TCP sockets that is used to connect to peer nodes. 

#### Initialization
A Peer Connection instance can be initialized with
* an existing already connected socket (i.e. when receiving), or 
* with an IP address and port combination in which it will create a new socket.

#### Message format
The data to be sent is assumed to be a JSON object. Thus `send_data(msg)` assumes that that `msg` is in a JSON format and `recv_data()` returns a JSON object and

---

### [Chat Peer](chat_peer.py)
The above two modules can ideally be used for any P2P application.  For this project, I have opted to build a small chat application. 

#### Supported Message Types
A Chat Peer extends the functionality of a Peer, and handles the following message types.
* `TEST` : Simply prints out the message that was received. For testing purposes.
* `PING` : sends a ping to a given IP address/Port with the source's peer name as the message payload
* `PONG` : upon receiving a ping, adds peer to list of known peers and returns a pong with the listening IP/Port of itself
* `ADVERTISE`: request peer for it's list of peers
* `ADVERTISE_REPLY`: upon receiving a IP/Port combination of a known peer, attempt to connect to it
* `BROADCAST`: prints out message that was received, and forwards it to list of known peers.

#### Methods for general use
The following methods are used to send messages to other peers:
* `join(host, port)`: sends a ping to connect to a given host/port combination
* `broadcast(msg)`: sends a message to all nodes in the network
* `get_peers_from(peerid)`: if peerid is in a node's list of peers, request that peer for its list of peers and connect to them
* `bootstrap(list)`: takes in a list of tuples for IP/port number combinations to automatically connect to.

## Demonstration and Tests 
A demo python script can be found in [demo.py](demo.py). 

Tests are written using Pytest and can be found in the file [test_peer.py](test_peer.py) 

## Future Work/Task List
Chat Peer:
- [x] Pings and registers peer when given IP/Port combo
- [x] Registers peer and replies with Pong when pinged
- [x] Bootstraps to pre-defined nodes
- [x] Advertises its list of peers
- [x] Automatically tries to connect to advertised peers
- [x] Broadcasts messages to own list of peers
- [x] Received broadcast message is forwarded to other peers
- [x] Handled case when multiple of the same broadcast message arrives from different peers
- [ ] Keep-alive checks to see if peers have dropped off
- [ ] One to one messaging between peers
