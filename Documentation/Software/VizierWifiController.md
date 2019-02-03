# Running the code
1. Make sure that the address the node is connecting to is correct correct address for where Mosquitto will be running
in the `vizier.node.Node()` call.
   * Found [here][1] on the Raspberry Pi
   * Found [here][2] on the Topside Computer for the guiController
2. Launch Mosquitto by running `Mosquitto -p 1884`
3. Start the Nodes. They will need to be started at about the same time as the nodes will timeout if they do not recieve a response
quickly enough.
   * Topside Computer: `python3 guiController.py`
   * Raspberry Pi: `python3 robot.py`

[1]: https://github.com/chachmu/SwimmingSwarm/blob/04b4c606ec923ecefc45c05d37f08ebd242f9115/robot.py#L34
[2]: https://github.com/chachmu/SwimmingSwarm/blob/04b4c606ec923ecefc45c05d37f08ebd242f9115/guiController.py#L72
