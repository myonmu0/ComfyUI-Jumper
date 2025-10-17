
# ComfyUI-Jumper
Designed to integrate local ComfyUI with remote ComfyUI(ex: Runpod, Vast.ai)<br />
Pass string and images between multiple ComfyUI via socket.

*On Remote*
![example](https://github.com/myonmu0/ComfyUI-Jumper/blob/main/examples/remote.png)
*On Local*
![example](https://github.com/myonmu0/ComfyUI-Jumper/blob/main/examples/local.png)


## Install
Clone this repo to ComfyUI custom_nodes/ directory.


## Usage
1. Rent one server, or start 2 ComfyUI on local.<br />

2. Open a port on remote, MUST use a secure channel like SSH Tunnel.
```
ssh root@REMOTE_IP -p REMOTE_PORT -NL 8282:localhost:8282
```
 - *Default port are 8282, however you can change this in nodes.py DEFAULT_ADDR val, or manually change on node.*
 - *If you will integrate local with local, skip this.*<br />

3. Start local and remote ComfyUI. As tutorial, load the examples/local.json to local ComfyUI, examples/remote.json to remote ComfyUI and run both to see if works.
 - *Accessing remote ComfyUI with SSH Tunnel are secure, easy and simple way that works on all cloud provider.*
 - *Accessing remote ComfyUI with browser's private/secret mode is a cleaner option because starts with 0 browser data, and ends with 0 data.*<br />

⚠️ **Known Issue:**
 Job cancel button don't work when this node are running, in such case send dummy data to "addr" or restart ComfyUI.


## Details 
1 Jumper node chain on 1 workflow.

Select all node "mode" to "Client" on local, and "Server" on remote.

The node "order" determine the order of sending/receiving data, and must be chain correctly on both side. Don't forget to add at least 1 node on the end of Jumper node chain(like in the example)

| send_as | Size        | CPU         | About                                    |
| --------- | -------------  | --------------- | ------------------------------------------------- |
| png     | Small       |  Moderate   | Convert tensor to png before sending.	<sub>Progress bar: 1 = Conversion, 2 = Sending</sub>    |
| zlib    | Large       |  Moderate   | Compress tensor before sending.          |
| raw     | Very Large  |  Very Low   | Raw tensor are send.  | 


