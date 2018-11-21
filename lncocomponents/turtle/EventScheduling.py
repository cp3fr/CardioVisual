# import libraries
from datetime import datetime
from time import time


#
class EventScheduling(object):

    #initialize by giving a path to the randomization file
    def __init__(self):

        self.currentEvent = 0
        self.name =    ['InitWait', 'GoToStart', 'Action', 'FinalWait']
        self.cross =   [True, True, True, False]
        self.command = [True, True, False, False]
        self.turtle =  [False, False, True, False]
        self.distance = 0.1
        self.tstart = time()    

    def setEvent(self, val):
        self.currentEvent = val
        self.tstart = time()
        
    def getEvent(self):
        return self.currentEvent
        
    def setDistance(self, val):
        self.distance = val
        
    def getDistance(self):
        return self.dist
        
    def showCross(self):
        return self.cross[self.currentEvent]
    
    def showCommand(self):
        return self.command[self.currentEvent]
        
    def showTurtle(self):
        return self.turtle[self.currentEvent]
        
    def showName(self):
        return self.name[self.currentEvent] 
      
    def evalDistance(self, val):
        if val < self.distance:
            return True
        else:
            return False
            
    def evalDuration(self, val):
        if time() - self.tstart > val:
            return True
        else:
            return False
