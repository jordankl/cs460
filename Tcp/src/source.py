"""
  Implements a basic TCP source

  Author: Daniel Zappala, Brigham Young University
  
  This program is licensed under the GPL; see LICENSE for details.

"""

# Python imports
import optparse
import sys

# local imports
from link import *
from tcp import *

class Source:
    def __init__(self,link,size,):
        self.link = link
        self.tcp = TCP(link)
        self.tcp.start()
        self.socket1 = TCPSocket(link,self.tcp,size,1,1)
        self.socket2 = TCPSocket(link,self.tcp,size,2,2)

    def start(self):
        self.socket2.send("hello 2")
        self.socket1.send("hello 1")
        # wait for link to be idle before ending
        self.link.idle()


def parse_options():
    """ Parse options. """
    parser = optparse.OptionParser(usage = "%prog [options]",
                                   version = "%prog 0.1")

    parser.add_option("","--from",type="string",dest="fromaddr",
                      default="localhost:5000",
                      help="host:port of the this side of the link")
    parser.add_option("","--to",type="string",dest="toaddr",
                      default="localhost:4000",
                      help="host:port of the other side of the link")
    parser.add_option("","--rate",type="float",dest="rate",
                      default=1.0,
                      help="bandwidth of the link in Mbps")
    parser.add_option("","--delay",type="int",dest="delay",
                      default=100,
                      help="propagation delay of the link in ms")
    parser.add_option("","--size",type="int",dest="size",
                      default=100,
                      help="size of the link queues")
    parser.add_option("","--log",type="string",dest="log",
                      default=None,
                      help="log file")
    parser.add_option("","--tcp-size",type="int",dest="tcp_size",
                      default=100,
                      help="size of the TCP queues")
    parser.add_option("","--verbose",action="store_true",dest="verbose",
                      default=False,
                      help="print statistics")

    (options,args) = parser.parse_args()
    return options

if __name__ == '__main__':
    # parse options
    options = parse_options()
    if options.fromaddr == None or options.toaddr == None:
        print "usage: sink.py --from host:port --to host:port [--rate rate] [--delay delay] [--size size]"
        sys.exit()

    # setup variables
    from_addr,from_port = options.fromaddr.split(':')
    from_port = int(from_port)
    to_addr,to_port = options.toaddr.split(':')
    to_port = int(to_port)

    # create link
    l = Link(size=options.size,rate=options.rate,delay=options.delay,
             log_name=options.log,
             from_addr=from_addr,from_port=from_port,
             to_addr=to_addr,to_port=to_port)

    # create and run source
    s = Source(l,options.tcp_size)
    s.start()
