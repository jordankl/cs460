import optparse
import readline
import sys

# local imports
import dv
import ping
import router

class Controller:
    """ A controller that sets up a virtual network of routers, runs a
    routing protocol, and allows tests with ping.  The controller accepts
    the following commands at the prompt:
    
    * start [id] [id] ... [id] : start routers with given ids
    * stop [id] [id] ... [id]  : stop routers with given ids
    * ping [times] [from] [to] : ping a number of times from one
                                 router to another
    * quit                     : quit the program
    """
    def __init__(self):
        """ Initialize the controller, parse command line options, and
        create the network.
        """
        self.routers = {}
        self.pingers = {}
        self.parse_options()
        self.create_network(self.options.config)
    
    def parse_options(self):
        """ Parse command line options:

        * -c or --config  : configuration file for the network
        * -v or --verbose : turn on debugging
        """
        parser = optparse.OptionParser(usage = "%prog [options]",
                                       version = "%prog 0.1")

        parser.add_option("-c","--config",type="string",dest="config",
                          default=None,
                          help="configuration file for the network")
        parser.add_option("-v","--verbose",action="store_true",dest="verbose",
                          default=False,
                          help="print debugging info")

        (options,args) = parser.parse_args()
        self.options = options

    def create_network(self,file):
        """ Create a virtual network from a configuration file.
        """
        if not file:
            print "No network configuration!"
            return
        f = open(file)
        for line in f.readlines():
            if line.startswith("#"):
                continue
            fields = line.split()
            # create router
            if fields[0] == "router":
                if len(fields) < 4:
                    continue
                id = fields[1]
                address = fields[2]
                try:
                    port = int(fields[3])
                except:
                    continue
                r = router.Router(id,address,port,self.options.verbose)
                r.start()
                self.routers[id] = r
            # create link
            if fields[0] == "link":
                if len(fields) < 3:
                    continue
                id1 = fields[1]
                id2 = fields[2]
                if id1 not in self.routers or id2 not in self.routers:
                    continue
                address = self.routers[id2].address
                port = self.routers[id2].port
                self.routers[id1].add_link(id2,address,port)
        # create routing
        for id in self.routers.keys():
            d = dv.DV(self.routers[id])
            p = ping.Ping(self.routers[id])
            self.pingers[id] = p

    def commands(self):
        """ Read and process commands from the terminal. """
        print "Welcome to the routing lab!"
        while True:
            # line = sys.stdin.readline()
            line = raw_input("> ")
            if line == "":
                continue
            if line.startswith("help"):
                print "Commands:"
                print "  start [id] [id] ... [id] -- start routers with given ids"
                print "  stop [id] [id] ... [id]  -- stop routers with given ids"
                print "  ping [times] [from] [to] -- ping a number of times from one router to another"
                print "  quit                     -- quit the program"
                continue
            if line.startswith("quit"):
                self.quit()
                break
            if line.startswith("stop"):
                fields = line.split()
                self.stop(fields[1:])        
                continue
            if line.startswith("start"):
                fields = line.split()
                self.restart(fields[1:])        
                continue
            if line.startswith("ping"):
                fields = line.split()
                if len(fields) < 4:
                    print "usage: ping [times] [from] [to]"
                    continue
                self.ping(fields[1],fields[2],fields[3])
                continue
            print "Unknown command"

    def quit(self):
        """ Execute the quit command. """
        print "Quitting ..."
        for id in self.routers.keys():
            self.routers[id].quit()

    def stop(self,ids):
        """ Execute the stop command. """
        for id in ids:
            if id not in self.routers:
                print "Unknown id",id
                continue
            print "Stopping",id
            self.routers[id].stop()

    def restart(self,ids):
        """ Execute the start command. """
        for id in ids:
            if id not in self.routers:
                print "Unknown id",id
                continue
            print "Starting",id
            self.routers[id].restart()

    def ping(self,times,id_from,id_to):
        """ Execute the ping command. """
        try:
            times = int(times)
        except:
            print "Number of times to ping must be an integer"
            return
        if id_from not in self.routers:
            print "Unknown id",id_from
            return
        if id_to not in self.routers:
            print "Unknown id",id_to
            return
        self.pingers[id_from].ping(id_to,times)

if __name__ == "__main__":
    c = Controller()
    c.commands()
