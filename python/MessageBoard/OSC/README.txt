
This directory contains a rudimentary MessageBoard <--> OSC gateway.

To run it, run MB_OSC_Gateway.py

By default it, will connect to a MessageBoard server on localhost, and
listen to OSC packets sent to port 9001.   All messages received from
the MessageBoard will be mapped to OSC packets and sent to an OSC socket
on localhost with port 9000.

localhost MessageBoard  ---->  localhost OSC 9000
localhost OSC 9001      ---->  localhost MessageBoard

Currently the mapping between MB messages and OSC packets is:

MessageBoard Message:
{"key1": val1, "key2": val2, ... "keyN": valN} <--->
              OSC Packet: (key1, val1, key2, val2, ..., keyN, valN)

and is only implemented correctly for values of type float, string, or
integer.   We still need to figure out a mapping to encode key values
of type vector.

