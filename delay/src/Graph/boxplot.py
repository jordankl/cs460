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
        self.count = 0
        self.intensity = [.25, .50, .75, .85, .90, 1.00, 1.05, 1.10, 1.25, 1.50, 1.75]
        self.intensityIndex = 0
    
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
            self.delays.append(self.d_queue.values())
            self.count += 1 
            self.d_queue = {}
            self.dropped = {}
            self.idCheck = -1
            
    def boxplot(self):
        """ Create a box plot of the download time"""
        boxplot(self.delays, sym='', positions=self.intensity, widths = .05)
        xticks([0,.25,.50,.75,1,1.25,1.5,1.75,2])
        xlabel('Traffic Intensity')
        ylabel('Queueing Delay (milliseconds)')
        savefig('boxplot_10.png')

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
    p.boxplot()