import socket
import sys
import threading
import time

""" A router provides packet forwarding for applications.  Each router
is identified by a text identifier (id) and listens for incoming
packets on a UDP socket using the provided (address) and (port).

When routers send packets, they include the following header:

  vr from_id to_id app

The (from_id) is the identifier of the source router and the (to_id)
is the identifier of the destination router.  The (app) is a text
identifier for the application that the packet should be delivered to,
once it reaches the destination router.

To send a packet to the next hop, a router looks up the (address) and
(port) of the next hop and sends a UDP packet.  Each time a router
forwards a packet, it adds 50 ms seconds of delay, so that the RTT for
a message on a path of length n hops is n*100 ms.

The router also supports path tracing, similar to traceroute.  If
requested by the application, the router adds a "trace" header to the
packet, and accumulates the list of router ids that the packet follows
while it is being forwarded. This path is given to the receiving
application in the receive() method.

The router supports the following public methods:

* register_handler(app,handler)

  Registers a handler with the router.  When the router receives an
  incoming packet with the identifier (app), it calls the receive()
  method on the given (handler) object.

* add_route(id,next)

  Adds a route from the current router to the destination identified
  by (id).  The route uses the identifier (next) to indicate the next
  router on the path toward the destination.

* delete_route(id)

  Deletes a route from the current router for the destination
  identified by (id).

* get_route(id)

  Returns the next hop identifier for the route to destination (id).

* add_link(id,address,port)

  Adds a link from this router to the neighbor identified by (id).
  The (address) and (port) identify the UDP socket on which the
  neighbor is listening.  This is used when forwarding packets to that
  router.  This method should only be called by the controller that
  sets up the network and NOT by the routing protocol.

* get_neighbors()

  Returns a list of neighbor ids, one for each of the direct neighbors
  of this router.

* send_packet(id,app,data,trace)

  Send a packet to an application listening on router (id).  The
  application is specified by the (app) and the (data) is a string.
  The (trace) parameter is a boolean that indicates whether to trace
  the route.

* stop()

  Stop handling packets.  This is useful for simulating a failed
  router for the routing protocol.

* restart()

  Restart a router that has been stopped.

* quit()

  Tell a router to quit.

"""

class Router(threading.Thread):
    """ Emulate a router by sending UDP packets.
    """
    def __init__(self,id,address,port,verbose):
        """ Initialize the router using:

        * id       : text identifier of the router
        * address  : IP address for the UDP socket
        * port     : port for the UDP socket
        * verbose  : turn on debugging
        """
        threading.Thread.__init__(self)
        threading.Thread.daemon = True
        self.id = id
        self.address = address
        self.port = port
        self.verbose = verbose
        # handlers
        self.handlers = {}
        # links
        self.links = {}
        # forwarding table
        self.forwarding = {}
        self.forwarding_sem = threading.Semaphore()
        # UDP socket variables
        self.size = 1500
        self.udp = None
        self.running = True
        self.handling = True
        self.create_socket()
        self.udp_sem = threading.Semaphore()

    # public methods

    def register_handler(self,app,handler):
        """ Register a (handler), which will receive packets for (app)
        """
        self.handlers[app] = handler

    def add_route(self,id,next):
        """ Add a router for destination (id).  The (next) hop is also
        a router identifier.
        """
        self.forwarding_sem.acquire()
        self.forwarding[id] = next
        self.forwarding_sem.release()

    def delete_route(self,id):
        """ Delete a route for destination id).
        """
        self.forwarding_sem.acquire()
        if id in self.forwarding:
            del self.forwarding[id]
        self.forwarding_sem.release()

    def get_route(self,id):
        """ Get the route for destination (id), returning the
        identifier for the next hop.
        """
        next = None
        self.forwarding_sem.acquire()
        if id in self.forwarding:
            next = self.forwarding[id]
        self.forwarding_sem.release()
        return next

    def add_link(self,id,address,port):
        """ Add a link to the neighbor router identified by (id) and
        listening with a UDP socket using (address) and (port).
        """
        self.links[id] = (address,port)
        self.add_route(id,id)

    def get_neighbors(self):
        """ Get the neighbors of this router.  Return a list of their
        identifiers.
        """
        return self.links.keys()

    def send_packet(self,id,app,data,trace):
        """ Send a packet of (data) to the (app) listening on
        destination router (id).
        """
        packet = "vr %s %s %s\n" % (self.id,id,app)
        if trace:
            packet += "trace\n"
        packet += data
        self.handle(packet)

    def stop(self):
        """ Stop this router from handling any packets.
        """
        self.handling = False

    def restart(self):
        """ Restart this router so it handles incoming packets again.
        """
        self.handling = True

    def quit(self):
        """ Quit the router.
        """
        self.running = False

    # private methods

    def create_socket(self):
        """ Create the UDP socket for this router.
        """
        try:
            self.udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.udp.bind((self.address,self.port))
            self.udp.settimeout(1)
        except:
            print "[%s]: can't create UDP socket" % (self.id)
            print "Error: ",sys.exc_info()[0],sys.exc_info()[1]
            if self.udp:
                self.udp.close()

    def run(self):
        """ Run this router in a thread, handling all incoming UDP
        packets.
        """
        if not self.udp:
            return
        while self.running:
            try:
                packet,address = self.udp.recvfrom(self.size)
            except socket.timeout:
                continue
            except:
                print "[%s]: UDP socket failed" % (self.id)
                print "Error: ",sys.exc_info()[0],sys.exc_info()[1]
                self.running = False
                continue
            self.handle(packet)

    def handle(self,packet):
        """ Handle the (packet).  Deliver to a local application if its
        destination id is the same as mine.  Otherwise, forward it to
        the next hop.
        """
        if not self.handling:
            return
        # find the header
        index = packet.find("\n")
        name,from_id,to_id,app = packet[0:index].split()
        # modify the trace if present
        if packet[index+1:].startswith("trace"):
            fields = packet.split("\n")
            path = fields[1] + " %s" % (self.id)
            new = fields[0] + "\n" + path + "\n" + "\n".join(fields[2:])
            packet = new
        # deliver data that is addressed to me
        if to_id == self.id:
            self.deliver(from_id,app,packet[index+1:])
            return
        # forward data that is not addressed to me
        time.sleep(0.05)
        self.forward(to_id,packet)

    def deliver(self,from_id,app,data):
        """ Deliver the (data) to a listening (app).  The (from_id) is
        the id of the router that sent the packet.  The (data) has the
        header removed already.
        """
        # find the application
        if app not in self.handlers:
            print "[%s]: no handler for application %s" % (self.id,app)
            return
        # get trace
        path = None
        if data.startswith("trace"):
            index = data.find("\n")
            path = data[:index]
            data = data[index+1:]
        # deliver the data
        if self.verbose:
            print "[%s]: delivering packet to %s" % (self.id,app)
        self.handlers[app].receive(from_id,data,path)

    def forward(self,id,packet):
        """ Forward a (packet) to destination (id).
        """
        # look up entry in forwarding table
        next = self.get_route(id)
        if not next:
            print "[%s]: no route for id %s" % (self.id,id)
            return
        address,port = self.links[next]
        if self.verbose:
            print "[%s]: forwarding packet for %s to %s" % (self.id,id,next)
        # send the packet
        self.send(address,port,packet)

    def send(self,address,port,packet):
        """ Send a (packet) to a neighbor router listening on a UDP
        socket identified by (address) and (port).
        """
        self.udp_sem.acquire()
        self.udp.sendto(packet,(address,port))
        self.udp_sem.release()
