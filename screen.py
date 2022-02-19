import zmq
import sys
import shared

my_port = shared.screen_port
pub_port = shared.sub_port
print("Screen node is running... [Server Port: %s] [Publisher Port: %s]" % (my_port, pub_port))

# Prepare our context and sockets
context = zmq.Context()

# Publisher Socket
pub_socket = context.socket(zmq.PUB)
pub_socket.bind("tcp://*:%s" % pub_port)

socket = context.socket(zmq.REP)
socket.bind("tcp://*:%s" % my_port)

while True:
    #  Wait for next request from client
    message = socket.recv().decode()
    if "leave" in message:
        str_split = message.split('|')
        print("--------------------------------")
        print("[%s] Node %s left the chat!" % (str_split[2],str_split[1]))
        print("--------------------------------")
    elif "new_node" in message:
        str_split = message.split('|')
        print("-----------------------------------")
        print("[%s] Node %s entered the chat!" % (str_split[2],str_split[1]))
        print("-----------------------------------")
    else:
        string_tokens = message.split('|')
        out_string = "[%s] Node %s message: %s" % (string_tokens[1], string_tokens[0], string_tokens[2])
        print("-----" + out_string)
        # Broadcast message to all subscribed nodes
        pub_socket.send_string(out_string)
    # Send an acceptance reply
    socket.send_string("Accepted")
