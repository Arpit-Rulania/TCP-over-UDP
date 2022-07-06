# TCP-over-UDP
Implementation of TCP protocol in python using UDP as a base.

# TO RUN:
python3 receiver.py receiver_port FileReceived.txt
python3 sender.py receiver_host_ip receiver_port FileToSend.txt MWS MSS timeout pdrop seed

# What is this project about?
This project will focus on implementing a reliable transport protocol over the UDP protocol.

This project will implement Padawan Transport Protocol (PTP), a piece of software that consists of a sender and receiver component that allows reliable unidirectional data transfer. PTP includes some of the features of the TCP protocol. This project uses the created PTP protocol to transfer simple text (ASCII) files from the sender to the receiver. PTP is implemented as two separate programs: Sender and Receiver. It implements unidirectional transfer of data from the Sender to the Receiver. Data segments will flow from Sender to Receiver while ACK segments will flow from Receiver to Sender. PTP is implemented on top of UDP. TCP sockets are not used.
<img width="806" alt="Screen Shot 2022-07-06 at 4 58 02 pm" src="https://user-images.githubusercontent.com/91777055/177489750-39b96980-7eeb-4d30-bc6b-418d586b405e.png">
