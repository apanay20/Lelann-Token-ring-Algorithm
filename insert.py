import zmq
import sys
import signal
import time
from datetime import datetime
import threading
import shared
import os
import random

insertInitialized = False
haveTheToken = False
previousLeaving = False
publicToken = 0
node_id = -1
my_port = -1
receiver_port = -1
screen_port = shared.screen_port
sub_port = shared.sub_port
directory = "./Data"

# Just an automate way to initialize the node
# Find the next available port number to reserve.
# Then select a random port number from active nodes
# to connect on.
def initializeNewNode():
    global node_id
    global my_port
    global receiver_port
    max_port = 0
    max_node = 0
    ports = []
    for f in os.listdir(directory):
        tempId = int(f.split('.')[0]) 
        if tempId > max_node:
            max_node = tempId

        tempFile = open(directory + "/" + f, 'r')
        line = tempFile.read()
        firstPort, secondPort = line.split(' ')
        ports.append(int(firstPort))
        ports.append(int(secondPort))
    
    node_id = str(max_node + 1)
    noDupPorts = list(dict.fromkeys(ports))
    noDupPorts.sort(reverse=True)

    my_port = str(noDupPorts[0] + 1)
    receiver_port = str(random.choice(noDupPorts))

if len(sys.argv) > 1:
    node_id = sys.argv[1]
    my_port = sys.argv[2]
    receiver_port = sys.argv[3]
else:
    initializeNewNode()
    
dataFileName = directory + "/" + node_id + ".txt"

# Prepare our context and sockets
context = zmq.Context()

# Subscriber socket
sub_socket = context.socket(zmq.SUB)
sub_socket.connect("tcp://localhost:%s" % sub_port)

# Screen node socket
screen_socket = context.socket(zmq.REQ)
screen_socket.connect("tcp://localhost:%s" % screen_port)

# Socket to sent token
send_socket = context.socket(zmq.PUSH)
send_socket.connect("tcp://localhost:%s" % receiver_port)

def getCurrentTime():
	now = datetime.now()
	current_time = now.strftime("%H:%M:%S")
	return current_time

# =========================INSERT CODE========================
print("Trying to enter the ring...")
receive_socket = context.socket(zmq.REP)
receive_socket.bind("tcp://*:%s" % my_port)
start_time = time.time()
# Inform next node that I entered the chat
# Bind my listening port to his listening port
# Tell to the next node to bind on my listening address
send_socket.send_string("new_node:" + my_port + "|" + node_id)
# First enter a loop until receive the acceptance from the node that I want to enter
# or a specific amount of time has passed, something that means the node is not available
accepted_entrance = False
while accepted_entrance == False:
    if (time.time() - start_time) >= 3 and accepted_entrance == False:
        print("The node that you want to connect is not active!")
        print("Exiting...")
        receive_socket.close()
        send_socket.close()
        time.sleep(5)
        sys.exit(0)
    try:
        message = receive_socket.recv_string(zmq.DONTWAIT)
        if len(message) > 0:
            accepted_entrance = True
    except zmq.Again:
        pass

receive_socket.close()
# Give the node some time to change ports
time.sleep(1)

receive_socket = context.socket(zmq.PULL)
receive_socket.bind("tcp://*:%s" % receiver_port)
send_socket.close()
send_socket = context.socket(zmq.PUSH)
send_socket.connect("tcp://localhost:%s" % my_port)
send_message = "new_node|" + node_id + "|" + getCurrentTime()
screen_socket.send_string(str(send_message))
acceptance = screen_socket.recv()
# =========================INSERT CODE========================

# Catch SIGINT signal to exit the ring
def signal_handler(sig, frame):
    if previousLeaving == True:
        print("You cannot leave at current state!")
        print("Try again in few seconds")
        return
    num_of_active_nodes = len(os.listdir(directory))
    if num_of_active_nodes <= 2:
        print("Only 2 nodes remained. You can not exit!")
        return
    print("I am leaving!")
    print("Unbinding...")
    deleteMyFile()
    wantToleave()
    print("Bye")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# Code to run when token received
def tokenReceived(token):
	global haveTheToken
	global publicToken
	haveTheToken = True
	publicToken = int(token)
	try:
		message = input("[Receive token: " + str(publicToken) + "] Enter a message and press ENTER.\n")
		if len(message) > 0:
			send_message = node_id + "|" + getCurrentTime() + "|" + message
			screen_socket.send_string(str(send_message))
			acceptance = screen_socket.recv()		
	except EOFError as e:
		pass

	publicToken += 1
	# Send token
	send_socket.send_string("token:" + str(publicToken))
	haveTheToken = False

# Function to run once the node want to leave
def wantToleave():
    #Close socket
	receive_socket.close()
	#Send my listening port so the next node can bind
	if haveTheToken == False:
		send_socket.send_string("leave:" + receiver_port)
	else:
		#If leaving while having the token, then send both my listening port
		#and token to the next node
		global publicToken
		publicToken += 1
		send_socket.send_string("token:" + str(publicToken) + "|leave:" + receiver_port)
    
	#Inform screen that I am leaving(Just for logging)
	send_message = "leave|" + node_id + "|" + getCurrentTime()
	screen_socket.send_string(str(send_message))
	acceptance = screen_socket.recv()	

# Function to run once the previous node want to leave
# Close current listening port and bind it to the port he previous node was listening
def previousLeft(port):
    global receive_socket
    global my_port
    my_port = port
    receive_socket.close()
    receive_socket = context.socket(zmq.PULL)
    receive_socket.bind("tcp://*:%s" % port)
    print("-------------------------------------------")
    print("Previous node left, now Listening to: ", port)
    print("-------------------------------------------")
    return receive_socket

# Function to run once a new node entered in the ring before current node
# Close current listening port and bind it to the port that new node is listening
def newNodeEntered(port, id):
	global receive_socket
	global my_port
	accept_entry_socket = context.socket(zmq.REQ)
	accept_entry_socket.connect("tcp://localhost:%s" % port)
	accept_entry_socket.send_string("Accept_Entry")
	accept_entry_socket.close()

	my_port = port
	receive_socket.close()
	receive_socket = context.socket(zmq.PULL)
	receive_socket.bind("tcp://*:%s" % port)
	print("-------------------------------------------------")
	print("Node %s entered before me, now Listening to: %s" % (id, port))
	print("-------------------------------------------------")
	return receive_socket

def deleteMyFile():
	os.remove(dataFileName)

def updateDataFile():
	f = open(dataFileName, "w")
	f.write(my_port + " " + receiver_port)
	f.close()

updateDataFile()

def showData():
    insertInitialized = True
    print("Node ID:   " + node_id)
    print("Listening: " + receiver_port)
    print("Sending:   " + my_port)
    print("---------------")

showData()

# Subscribe to every topic(receive all)
sub_socket.setsockopt_string(zmq.SUBSCRIBE, "")
while True:
    while True:
        try:
            chat_string = sub_socket.recv_string(zmq.DONTWAIT)
			# Print only if not my message
            string_tokens = chat_string.split(' ')
            if string_tokens[2] != node_id:
                print("-----" + chat_string)
        except zmq.Again:
            break
    
    while True:
        try:
			# receive token
            recv_str = receive_socket.recv_string(zmq.DONTWAIT)
            #Previous node left while having the token
            # Create a thread to manage token job so input() not block the listening function of the node
            if ("token" in recv_str) and ("leave" in recv_str):
                previousLeaving = True
                tokenTemp, portTemp = recv_str.split('|')
                receive_socket = previousLeft(portTemp[6:])
                currentToken = tokenTemp[6:]
                tokenThread = threading.Thread(target=tokenReceived, name="TokenTask", args=(currentToken,))
                tokenThread.daemon = True
                tokenThread.start()
                updateDataFile()
                previousLeaving = False
			#Receive token from previous node
            # Create a thread to manage token job so input() not block the listening function of the node
            elif "token" in recv_str:
                currentToken = recv_str[6:]
                tokenThread = threading.Thread(target=tokenReceived, name="TokenTask", args=(currentToken,))
                tokenThread.daemon = True
                tokenThread.start()
			#Previous node left
            elif "leave" in recv_str:
                previousLeaving = True
                receive_socket = previousLeft(recv_str[6:])
                updateDataFile()
                previousLeaving = False
            elif "new_node" in recv_str:
                str_split = recv_str.split("|")
                new_node_id = str_split[1]
                if new_node_id == node_id:
                    receive_socket.close()
                    send_socket.close()
                    deleteMyFile()
                    try:
                        clear = lambda: os.system('cls')
                        clear()
                    except:
                        clear = lambda: os.system('clear')
                        clear()
                    print("You cannot enter the ring using this port at current time!")
                    print("Exiting...")
                    time.sleep(5)
                    sys.exit()
                receive_socket = newNodeEntered(str_split[0][9:], new_node_id)
                updateDataFile()
        except zmq.Again:
            break