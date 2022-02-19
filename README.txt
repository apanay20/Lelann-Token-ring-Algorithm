=========================================
	     MANUAL SETUP
=========================================
Run screen.py
-------------
python screen.py
Example: python screen.py

Run node.py
-----------
python node.py [ID] [NODE PORT] [NEXT NODE PORT]
Example: python node.py 0 5000 5001

Example with 3 nodes:
---------------------
python screen.py
python node.py 0 5000 5001
python node.py 1 5001 5002
python node.py 2 5002 5000

Delete Node:
------------
Press Ctrl-C in current node terminal

Insert Node:
------------
python insert.py 3 5003 5002

=========================================
	    AUTOMATED SETUP
=========================================
1) Edit initialize script and enter the number of nodes to be created
2) Run initialize script once
3) To insert a node just run the enterChat script

