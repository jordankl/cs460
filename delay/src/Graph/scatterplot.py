import optparse
import sys

import matplotlib
matplotlib.use('Agg')
from pylab import *

# Class that parses a file and plots several graphs
class Plotter:
    def __init__(self,file):
        """ Initialize plotter with a file name. """
        self.file = file
        self.files = []
        self.d_tran_prop = 3.201599
        self.d_queue = {}
        self.delays = []
        self.idCheck = -1
        self.dropped = {}
        self.count = 1;
    
    def parsefiles(self):
        first = None
        f = open(self.file)
        for line in f.readlines():
            line = line.strip("/home/jordan/workspace/delay/src/Graph/")
            line = line.rstrip()
            line = "l"+line
            self.files.append(line)
                    
    def parse(self):
        """ Parse the data file and accumulate values for the time,
            download time, and size columns.
        """
        for file in self.files:
            self.file =file
            f = open(file)
            for line in f.readlines():
                if line.startswith("TraceDelay: RX"):
                    try:
                        attributes = line.split()
                        delay_total = attributes[16]
                        id = attributes[8]
                    except:
                        continue
                    id = int(id)
                    if id != (self.idCheck+1):
                        droppedIds = id - (self.idCheck+1)
                        while droppedIds>0:
                            self.idCheck +=1
                            self.dropped[self.idCheck] = -.05
                            droppedIds -=1
                    self.idCheck += 1
                    delay_total = float(delay_total.strip('+ns'))
                    delay_total = delay_total/1000000
                    delay_queue = delay_total - self.d_tran_prop
                    self.d_queue[id] = delay_queue 
                else:
                    continue          
            self.scatterplot()
            self.count += 1 
            self.d_queue = {}
            self.dropped = {}
            self.idCheck = -1
    def scatterplot(self):
        """ Create a scatter plot graph. """
        clf()        
        scatter(self.d_queue.keys(),self.d_queue.values(), s=10, c='w', marker='o')
        if len(self.dropped) > 0:
            scatter(self.dropped.keys(),self.dropped.values(), s=10, c='r', marker='x')
        xlabel('Sequence Number')
        ylabel('Queueing Delay (milliseconds)')
        ylim( -.2,1400)
        savefig('scatter_1000_'+str(self.count)+'.png')
def parse_options():
        # parse options
        parser = optparse.OptionParser(usage = "%prog [options]",
                                       version = "%prog 0.1")

        parser.add_option("-f","--file",type="string",dest="file",
                          default=None,
                          help="file")

        (options,args) = parser.parse_args()
        return (options,args)


if __name__ == '__main__':
    (options,args) = parse_options()
    if options.file == None:
        print "plot.py -f file"
        sys.exit()
    p = Plotter(options.file)
    p.parsefiles()
    p.parse()