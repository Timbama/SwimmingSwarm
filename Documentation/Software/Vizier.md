# Installation
1. Clone or download the [repository][1].
2. Follow the installation instruction on the repository.
3. Install Mosquitto by running `sudo apt-get install mosquitto`

# Overview
Vizier is 
"A networking framework built on top of MQTT to allow the communication and synchronization of distributed,
language-independent resources"


Basically, it allows you to send messages between devices using an MQTT Server to mediate between them. The messages are sent back and forth
between "nodes" which in our use case are the Topside Computer and the robot. Each of the nodes has a JSON file that describes
what types of messages the node can send and recieve. This allows the python script to request a certain type of message from the
server which then sends back the correct information.

# JSON Description Files
## Purpose
The JSON Description files are used to describe what types of messages a node can send and recieve as well as the name of the node.

## Format
The JSON File is formatted in this order:

1. The `end_point` (the node) is given a name
2. A List of the "links" which are the possible messages it can send.
   1. The link has its own list of links
   2. The type that the link is. This can one of two types:
      * STREAM "publishes" the data given to it over the link
      * DATA "puts" the data on the link
   3. The requests that the node can make. These ask the server to respond with the data specified.

This is the JSON description file for the robot node:
```JSON
{
  "end_point" : "robot",
  "links" :
  {
    "/state" :
    {
      "links" : {},
      "type" : "STREAM"
    }
  },
  "requests" : [{"link": "controller/input", "type": "STREAM", "required": false}]
}

```
`controller` is the name of the other node that it is connecting to and it can request the data labeled `input`.

# Syntax
*All of the sample code shown here is pulled directly from the [robot.py][1] file*

First, you need to open the JSON file to get the information from it.

```python
node_descriptor = None
f = open("node_desc_robot.json", 'r')
node_descriptor = json.load(f)
f.close()
```

This code loads the node description information from a JSON file and stores it in `node_descriptor`.  

<br><br>
Next, you need to start the Vizier Node.  
```python
node = vizier.node.Node("localhost", 1884, node_descriptor)
```
The first argument is the address that the MQTT Server is running at. The second argument is the port number. Finally, the third argument is the node description information pulled from the JSON file as shown earlier.  

<br><br>
After this you need to set up the connections for sending and recieving.

```python
publishable_link = list(node.publishable_links)[0]
subscribable_link = list(node.subscribable_links)[0]
msg_queue = node.subscribe(subscribable_link)
```
The first two lines get the first publishable link and subscribable link from the list of each type of link in the JSON file.
Then, the last line sets up a message queue for the recieving link to put recieved messages into.  

<br><br>
Next, you need to send or recieve using the links that you have set up. 
```python
node.publish(publishable_link,"1")
message = msg_queue.get(timeout = 1).payload.decode(encoding='UTF-8')
```

The first line sends a string, `"1"`, over the `/state` link since it is the first publishable link in the JSON file.  

The second line recieves a message from the recieving link (timing out if it has not recieved a message after 1 second).
This message contains a payload (the information we want) which is in binary form. the call to decode() is to decode this binary
into a string using UTF-8.  

<br><br>
Finally, when we are done we need to close the connection.
```python
node.stop()
```
[1]: https://github.com/robotarium/vizier
[2]: https://github.com/chachmu/SwimmingSwarm/blob/849e48bec4546f2969349d917c4d93bd74bb12cf/robot.py
