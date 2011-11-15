"""
  Implements a thread safe logger

  Author: Daniel Zappala, Brigham Young University
  
  This program is licensed under the GPL; see LICENSE for details.

"""

import threading

class Log:
    def __init__(self,file):
        if file == None:
            self.file = None
            return
        self.file = file
        if self.file:
            self.fh = open(self.file,'w')
        self.sem = threading.Semaphore()
        
    def write(self,str):
        if not self.file:
            return
        self.sem.acquire()
        self.fh.write(str)
        self.sem.release()

