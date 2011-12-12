class DV:
    """ Implements a distance vector routing protocol.
    """
    def __init__(self,router):
        """ Initialize the protocol with the (router) object it is
        attached to.  Register the protocol as a handler for the 'dv'
        application identifier.
        """
        self.router = router
        self.router.register_handler('dv',self)
        self.dv()

    def dv(self):
        for r in self.router.get_neighbors():
            print self.router.id+":"+r
            self.router.send_packet(r,"dv",self.router.id,False)
        
    def receive(self,id,data,path):
        print "Data: "+data
        if path:
            print "Path: "+path
