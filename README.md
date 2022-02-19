## Description
This is an implementation of the Lelann's token-ring algorithm. The implementation take into account failure of processes, supports the insertion of a new process in the ring and every process can leave the ring at any time. Monitor script is not necessary for the algorithm, is used just for printing messages.

## Algorithm

* Processes are arranged in a logical ring
* At start, process 0 is given a token
  * Token circulates around the ring in a fixed direction via point-to-point messages
  * When a process acquires the token, it has the right to enter the critical section
  * After exiting critical section, it passes the token on

## Prerequisites

Below are shown the necessary python library to run the algorithm. 
* ZeroMQ
  ```sh
  pip install pyzmq
  ```
