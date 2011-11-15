"""
  Implements TCP running over an emulated link

  Author: Daniel Zappala, Brigham Young University
  
  This program is licensed under the GPL; see LICENSE for details.

"""

import Queue
import struct
import sys
import threading
import hashlib

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
            raise AddressInUse
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
        self.packetSize = 10
        self.bufferSize = size
        
    # sending data
    def send(self,data):
        """ Send a TCP packet. """
        # segment data into packet size and packs them into packets
        packets = self.packData(data)
        # send the packet
        id = 0
        print packets
        while id<len(packets):       
            self.link.enqueue(id,packets[id])
            id += 1
        return len(data)
    
    def packData(self,data):
        index = 0
        id = 1
        packetQueue = []
        total = len(data)/self.packetSize
        if len(data)%self.packetSize != 0 :
            total +=1
        head = self.makepacket(str(total), 0)
        packetQueue.append(head)        
        while index < len(data)-1 :
            if index+self.packetSize < len(data):
                packetData = data[index:index+self.packetSize]
            else :
                packetData = data[index:]
            # make a packet
            packet = self.makepacket(packetData,id)
            packetQueue.append(packet)
            index += self.packetSize
            id += 1
        return packetQueue
            

    def makepacket(self,data,id):
        u = TCPPacket()
        u.sourcePort = self.sourcePort
        u.destPort = self.destPort
        u.len = len(data) + 8
        u.data = data
        u.id = id
        u.hash = str(hashlib.sha224(data).hexdigest())
        u.cksum = len(u.hash)
        packet = u.pack()
        return packet
            
    # receiving data
    def recv(self,timeout):
        """ Receive a TCP packet and return the data. If no data is
        available, wait indefinitely for the next available packet."""        
        expectedId = 0;
        lastID = -1
        msg = ''
        packets = []
        packet = self.buffer.get(True,timeout)
        u = TCPPacket()
        try:
            u.unpack(packet)
            print u.data
#            if u.hash != str(hashlib.sha224(u.data).hexdigest()) :
#                print u.hash
#                print str(hashlib.sha224(u.data).hexdigest())
#                print "Packet was corrupted"
#                return
#            else:
#                if expectedId == u.id :
#                    if expectedId == 0 :
#                        lastID = int(u.data)
#                    else:
#                        msg += u.data
#                        if expectedId == lastID:
#                            expectedId = 0
#                            lastID -1
#                    expectedId += 1
#                    #TODO send ack packet
#                else :
#                    return
                    #TODO implement save pack for efficiency and afford packet duplication              
        except:
            print "Exception: unpacking a TCP packet"
            print "  ",sys.exc_info()[0],sys.exc_info()[1]
            return
        return ''


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
        self.data = ''
        self.hash = ''

        # packing information
        self.format = "!HHHHH"
        self.headerlen = struct.calcsize(self.format)

    def pack(self):
        """ Create a string from a TCP packet """
        string = struct.pack(self.format,self.sourcePort,self.destPort,
                             self.len,self.cksum,self.id)
#        print self.sourcePort,self.destPort,self.len,self.cksum,self.id,self.hash,self.data
        return string + self.hash + self.data

    def unpack(self,string):
        """ Create a TCP packet from a string """
        # unpack the header fields
        (self.sourcePort,self.destPort,self.len,self.cksum,self.id) = struct.unpack(self.format,string[0:self.headerlen])
        # unpack the data,
        self.hash = string[self.headerlen:self.cksum+self.headerlen]
        self.data = string[self.cksum+self.headerlen:]   
        print self.sourcePort,self.destPort,self.len,self.cksum,self.id,self.hash,self.data