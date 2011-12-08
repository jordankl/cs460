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
        self.queuePacks = []
        self.enqueuePacks = []
        self.dequeuePacks = []
        self.receivedPacks = []
        self.droppedPacks = []
        self.receivedRate = []
        self.ticks = []
        self.twentyone = []
        self.queue = []
        self.drops = []
        
    
 #   def parsefiles(self):
 #       first = None
 #       f = open(self.file)
 #       for line in f.readlines():
 #           line = line.strip("/home/jordan/workspace/delay/src/Graph/")
 #           line = line.rstrip()
 #           line = "l"+line
 #           self.files.append(line)
            
    def parse(self):
        """ Parse the data file and accumulate values for the time,
            download time, and size columns.
        """
#        for file in self.files:
        f = open(self.file)
        for line in f.readlines():
            packet = {}
            if line.startswith("+"):
                try:
                    e = line.split()
                    packet['time'] = float(e[1])
                    packet['length'] = int(e[23])
                    packet['type'] = "+"
                    packet['receiver'] = int(e[28][1:])
                    if(packet['receiver']> 20):
                        packet['receiver'] = packet['receiver']-49143
                    if(packet['length'] != 40):
                        self.enqueuePacks.append(packet)
                        self.queuePacks.append(packet)
                except:
                    continue
            elif line.startswith("-"):
                try:
                    d = line.split()
                    packet['time'] = float(d[1])
                    packet['length'] = int(d[23])
                    packet['type'] = "-"
                    packet['receiver'] = int(d[28][1:])
                    if(packet['receiver']> 20):
                        packet['receiver'] = packet['receiver']-49143
                    if(packet['length'] != 40):
                        self.dequeuePacks.append(packet)
                        self.queuePacks.append(packet)
                except:
                    continue
            elif line.startswith("r"):
                try:
                    r = line.split()
                    packet['time'] = float(r[1])
                    packet['length'] = int(r[18])
                    packet['receiver'] = int(r[23][1:])
                    if(packet['receiver']> 20):
                        packet['receiver'] = packet['receiver']-49143
                    if(packet['length'] != 40):
                        self.receivedPacks.append(packet)
                except:
                    continue
            else:
                try:
                    drop = line.split()
                    packet['time'] = float(drop[1])
                    packet['length'] = int(drop[23])
                    packet['receiver'] = int(d[28][1:])
                    if(packet['receiver']> 20):
                        packet['receiver'] = packet['receiver']-49143
                    if(packet['length'] != 40):
                        self.droppedPacks.append(packet)
                except:
                    continue
        print len(self.queuePacks)
        print len(self.enqueuePacks)
        print len(self.dequeuePacks)
        print len(self.receivedPacks)
        print len(self.droppedPacks)
        
    def plot(self):
        clf()        
        plot(self.ticks,self.receivedRate)
        xlabel('Time(seconds)')
        ylabel('receiving rate (bps)')
        savefig('lineplot.png')
        
    def scatterplot(self):
        """ Create a scatter plot graph. """
        clf()        
        plot(self.ticks,self.queue)
        scatter(self.drops, self.twentyone ,s=10, c='r', marker='x')
        xlabel('Time(seconds)')
        ylabel('Queue Size')
        savefig('scatter.png')
        
    def recieverRate(self):
        upperLimit = 1.0
        lowerLimit = 0.0
        while(True):
            sum = 0
            for pack in self.receivedPacks:
                if(pack['time']>=lowerLimit and pack['time']<=upperLimit):
                    sum+=1;
            self.receivedRate.append(sum)
            self.ticks.append(upperLimit)
            if(upperLimit >= 10):
                break
            else:
                upperLimit += .1
                upperLimit = round(upperLimit, 1)
                lowerLimit += .1
                lowerLimit = round(lowerLimit, 1)
#        print self.receivedRate
        
    def queueSize(self):
        self.ticks = []
        upperLimit = .1
        queue = 0;
        for drop in self.droppedPacks:
            self.drops.append(drop['time'])
            self.twentyone.append(21)
        for pack in self.queuePacks:
            if(pack['time']<=upperLimit):
                if(pack['type']=="+"):
                    queue+=1
                else:
                    queue-=1
            else:
                self.queue.append(queue)
                self.ticks.append(upperLimit)
                upperLimit += .1
                upperLimit = round(upperLimit, 1)
                if(pack['type']=="+"):
                    queue+=1
                else:
                    queue-=1
#        print self.queue
            
            

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
        print "plotter.py -f file"
        sys.exit()
    p = Plotter(options.file)
#    p.parsefiles()
    p.parse()
    p.recieverRate()
    #p.plot()
    p.queueSize()
    p.scatterplot()