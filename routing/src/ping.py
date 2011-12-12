import sys
import threading
import time

class Ping:
    """ A ping application for the routing project.
    """
    def __init__(self,router):
        """ Initialize ping by supplying the (router) object it is
        attached to.
        """
        self.router = router
        self.router.register_handler('ping',self)
        self.event = threading.Event()

    def ping(self,id,times):
        """ Perform a ping from this router to the destination router
        given by (id).  Repeat the given amount of (times).
        """
        for i in range(times):
            t1 = time.time()
            data = "ping\n%f\n" % (t1)
            self.router.send_packet(id,'ping',data,True)
            self.event.clear()
            self.event.wait(10)
            if self.event.is_set():
                continue
            print "No response"
    
    def receive(self,id,data,path):
        """ Receive a ping message from router (id) stored in (data).
        If it is a ping, then return a pong.  If it is a pong, then
        record and print the RTT.
        """
        if path:
            index = path.find(" ")
            print "Path:",path[index+1:]
        try:
            header,t1,empty = data.split("\n")
            t1 = float(t1)
        except:
            return
        if header.startswith("ping"):
            data = "pong\n%f\n" % (t1)
            self.router.send_packet(id,'ping',data,False)
            return
        if header.startswith("pong"):
            t2 = time.time()
            print "RTT:",t2-t1
            self.event.set()
            return
