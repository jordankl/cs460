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
        
    def receive(self,router,data,path):
        print "Data: "+data+"\n Path: "+path
