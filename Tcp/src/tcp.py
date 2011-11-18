"""
  Implements TCP running over an emulated link

  Author: Daniel Zappala, Brigham Young University
  
  This program is licensed under the GPL; see LICENSE for details.

"""

import Queue
import struct
import sys
import threading

__all__ = [ "TCP","TCPSocket" ]

class TCP(threading.Thread):
    """ Emulate TCP on a host. """
    def __init__(self,link):
        self.link = link
        threading.Thread.__init__(self)
        threading.Thread.daemon = True
        self.sem = threading.Semaphore()
        self.binding = {}

    def bind(self,port,socket):
        """ Bind a socket to the requested port.

        The result of the bind call is that any packets arriving at
        this node that have the destination port that matches the
        bound port will be passed to the supplied socket.

        Note: all access to memory that is shared among all sockets
        must be protected with a semaphore.

        """
        # lock
        self.sem.acquire()

        # make binding
        if (port) in self.binding:
            self.sem.release()
            raise 'AddressInUse'
        self.binding[port] = socket

        # unlock
        self.sem.release()

    def unbind(self,port):
        """ Remove the binding for a socket."""
        self.sem.acquire()
        if port in self.binding:
            del self.binding[port]
        self.sem.release()

    # this method will run when the thread is started
    def run(self):
        while (True):
            packet = self.link.dequeue(None)
            u = TCPPacket()
            try:        
                u.unpack(packet)
            except:
                print "Exception: unpacking a TCP packet"
                print "  ",sys.exc_info()[0],sys.exc_info()[1]
                return

            # find binding for port and deliver to appropriate socket
            if u.destPort in self.binding:
                try:
                    self.binding[u.destPort].buffer.put_nowait(packet)
                except Queue.Full:
                    # drop packet if full
                    pass


class TCPSocket:
    """ Emulate a TCP socket on a host."""
    def __init__(self,link,tcp,size,sourcePort,destPort):
        self.link = link
        self.buffer = Queue.Queue(size)
        self.sourcePort = sourcePort
        self.destPort = destPort
        self.tcp = tcp
        self.tcp.bind(sourcePort,self)
        self.packets = []
        self.packetsize = 1024

    # sending data
    def send(self,data):
        """ Send a TCP packet. """
        # make a packet
        self.segmentData(data)
        print self.packets
        # send the packet
        id = 0
        for packet in self.packets: 
            self.link.enqueue(id,packet)
            id += 1
        return len(data)
    
    def segmentData(self,data):
        """ Segment the Data"""
        index = 0;
        id = 1
        totalPackets = len(data)/self.packetsize
        totalPackets += 0 if (len(data)%self.packetsize == 0) else 1        
        while (index < len(data)):
            if ((index+self.packetsize)<len(data)):
                self.packets.append(self.makepacket(data[index:(index+self.packetsize)],id,totalPackets))
            else:
                self.packets.append(self.makepacket(data[index:len(data)],id,totalPackets))
            index += self.packetsize
            id +=1    
                            
    def makepacket(self,data,id,totalPackets):
        u = TCPPacket()
        u.sourcePort = self.sourcePort
        u.destPort = self.destPort
        u.len = len(data) + 8
        u.data = data
        # ignore checksum
        u.cksum = 0
        u.id = id
        u.totalPackets = totalPackets
        packet = u.pack()
        return packet
            
    # receiving data
    def recv(self,timeout):
        msg ='';
        data = 'will be overwritted'
        flag = False
        while(flag != True):
            data,flag = self.recvAll(timeout)
            msg += data
        return msg        
    
    def recvAll(self,timeout):
        """ Receive a TCP packet and return the data. If no data is
        available, wait indefinitely for the next available packet."""
        
        packet = self.buffer.get(True,timeout)
        u = TCPPacket()
        lastPacket = False
        try:        
            u.unpack(packet)
            if(u.id == u.totalPackets):
                lastPacket = True
        except:
            print "Exception: unpacking a TCP packet"
            print "  ",sys.exc_info()[0],sys.exc_info()[1]
            return

        return u.data,lastPacket


class TCPPacket:
    """ Class to represent a TCP packet.  Converts the packet from a
    set of member variables into a string of bytes so it can be sent
    over the socket."""
    def __init__(self):
        """ Initialize the packet """
        # TCP packet
        self.sourcePort = 0
        self.destPort = 0
        self.len = 0
        self.cksum = 0
        self.id = 0
        self.totalPackets = 0
        self.data = ''

        # packing information
        self.format = "!HHHHHH    "
        self.headerlen = struct.calcsize(self.format)

    def pack(self):
        """ Create a string from a TCP packet """
        string = struct.pack(self.format,self.sourcePort,self.destPort,
                             self.len,self.cksum,self.id,self.totalPackets)
        return string + self.data

    def unpack(self,string):
        """ Create a TCP packet from a string """
        # unpack the header fields
        (self.sourcePort,self.destPort,self.len,self.cksum,self.id,self.totalPackets) = struct.unpack(self.format,string[0:self.headerlen])
        # unpack the data
        self.data = string[self.headerlen:]