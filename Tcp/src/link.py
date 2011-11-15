"""
  Implements an emulated link

  Author: Daniel Zappala, Brigham Young University
  
  This program is licensed under the GPL; see LICENSE for details.

"""

import Queue
import socket
import sys
import threading
import time

from log import *

class Link:
    """
    Implements a virtual link between two machines, using UDP to
    transmit packets.
    """
    def __init__(self,size,rate,delay,log_name,
                 from_addr,from_port,to_addr,to_port):
        """
        Initialize the link:
        * size       the size of the queue used to store packets that are
                     going out or coming in over the link
        * rate       the rate of the link, in Mbps
        * delay      the propagation delay of the link, in ms
        * log_name   log file name
        * from_addr  the IP address on this side of the link
        * from_port  the UDP port on this side of the link
        * to_addr    the IP address on the other side of the link
        * to_port    the UDP port on the other side of the link
        """
        # setup member variables
        self.rate = rate
        self.delay = delay
        self.log = Log(log_name)
        self.from_addr = from_addr
        self.from_port = from_port
        self.to_addr = to_addr
        self.to_port = to_port
        # setup UDP socket
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)
            self.socket.settimeout(1)
            self.socket.bind((self.from_addr,self.from_port))
            self.socket.connect((self.to_addr,self.to_port))
        except:
            self.socket = None
            print "Can't initialize socket"
            print "Error: ",sys.exc_info()[0],sys.exc_info()[1]
        # start incoming handler
        self.in_queue = Queue.Queue(size)
        self.in_thread = Incoming(socket=self.socket,queue=self.in_queue,
                                  log=self.log)
        self.in_thread.start()
        # start outgoing handler
        self.out_queue = Queue.Queue(size)
        self.out_thread = Outgoing(socket=self.socket,queue=self.out_queue,
                                   log=self.log,rate=self.rate,delay=self.delay)
        self.out_thread.start()

    def enqueue(self,id,packet):
        """ Add id and packet to the outgoing queue.  If the queue is
        full, the packet is dropped."""
        now = time.time()
        try:
            self.log.write("%f %d added\n" % (now, id))
            self.out_queue.put_nowait((id,packet))
        except:
            self.log.write("%f %d dropped\n" % (now, id))
            pass

    def dequeue(self,timeout):
        """ Get packet from the incoming queue. Blocks until data is
        available. """
        try:
            packet = self.in_queue.get(True,timeout)
        except Queue.Empty:
            packet = None
        return packet

    def idle(self):
        while True:
            if self.out_thread.idle and self.in_thread.idle:
                return
            else:
                time.sleep(1)
    
class Outgoing(threading.Thread):
    """
    Handler for the outgoing queue of the link.  Takes packets from
    the queue, emulates the transmission delay, and then queues them
    for emulation of propagation delay.
    """
    def __init__(self,socket,queue,log,rate,delay):
        """
        Initialize the handler:
        * socket  the UDP socket used for the link
        * queue   the outgoing queue for the link
        * log     a logging object
        * rate    the rate of the link, in Mbps
        * delay   the propagation delay of the link, in ms
        """
        threading.Thread.__init__(self)
        threading.Thread.daemon = True
        # initialize member variables
        self.socket = socket
        self.queue = queue
        self.log = log
        self.rate = rate
        self.delay = delay
        self.idle = False
        # setup propagation delay queue and handler
        self.prop_queue = Queue.Queue()
        self.prop_thread = Propagation(socket=self.socket,queue=self.prop_queue,
                                       log=self.log,delay=self.delay)
        self.prop_thread.start()

    def run(self):
        """ Continuously read data from the queue and emulate
        transmission delay.  Once the transmission delay is finished,
        add the data to a propagation delay queue.  This method is
        activated by a call to start() and runs in a separate thread."""
        if not self.socket:
            return
        while True:
            # get data to send
            try:
                packet = self.queue.get(timeout=1)
                self.idle = False
            except Queue.Empty:
                self.idle = True
                continue
            id,data = packet
            now = time.time()
            self.log.write("%f %d sending\n" % (now, id))
            # calculate transmission delay
            trans = float(len(data)*8) / (1000*1000*self.rate)
            # sleep
            time.sleep(trans)
            now = time.time()
            self.log.write("%f %d sent\n" % (now, id))
            # queue for propagation delay
            now = time.time()
            self.prop_queue.put((id,data,now))

class Propagation(threading.Thread):
    """
    Handler to emulate propagation delay of the link.  Takes packets
    from the queue and emulates the delay, then sends them on the UDP
    socket.
    """
    def __init__(self,socket,queue,log,delay):
        """
        Initialize the handler:
        * socket  the UDP socket used for the link
        * queue   the outgoing queue for the link
        * delay   the propagation delay of the link, in ms
        """
        threading.Thread.__init__(self)
        threading.Thread.daemon = True
        self.socket = socket
        self.queue = queue
        self.log = log
        self.delay = float(delay)/1000

    def run(self):
        """ Continuously read data from the queue and emulate
        propagation delay.  Once the delay is finished, send it over
        the virtual link.  This method is activated by a call to
        start() and runs in a separate thread."""
        while True:
            # get data to send
            id,data,then = self.queue.get()
            now = time.time()
            if (now - then) < self.delay:
                time.sleep(self.delay - (now - then))
            # transmit the data over the socket
            try:
                self.socket.send(data)
            except:
                print "Can't send on UDP socket"
                print "Error: ",sys.exc_info()[0],sys.exc_info()[1]
                return

class Incoming(threading.Thread):
    """
    Handler for the incoming queue of the link.  Receives packets from
    the UDP socket and puts them on the queue.  If the queue is full then
    packets are dropped.
    """
    def __init__(self,socket,queue,log):
        """
        Initialize the handler:
        * socket  the UDP socket used for the link
        * queue   the incoming queue for the link
        * log     a logging object
        """
        threading.Thread.__init__(self)
        threading.Thread.daemon = True
        # initialize member variables
        self.log = log
        self.socket = socket
        self.queue = queue
        self.idle = False
        # set the maximum segment size for the link
        self.mss = 1500

    def run(self):
        """ Continuously receive data over the virtual link and add it
        to a queue.  This method is activated by a call to start() and
        runs in a separate thread."""
        if not self.socket:
            return
        while True:
            # receive incoming segment
            try:
                data,addr = self.socket.recvfrom(self.mss)
                self.idle = False
            except socket.timeout:
                self.idle = True
                continue
            except:
                print "Can't receive from UDP socket"
                print "Error: ",sys.exc_info()[0],sys.exc_info()[1]
                return
            now = time.time()
            self.log.write("%f received\n" % (now))
            # put data on incoming queue
            try:
                self.queue.put_nowait(data)
            except Queue.Full:
                pass
