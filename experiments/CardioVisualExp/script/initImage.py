#import libraries
import csv
from os import path
from time import time

# ======== Start of Replay Buffer class ==================================================

class ReplayBuffer(object):

    #initialization of variables
    def __init__(self):

        #list of last two onset timestamps
        self.beats = []
        
        #list of interbeat intervals for reading
        self.ibiRead = [] #default list
        for i in range(100):
            self.ibiRead.append(0.8)
        
        #list of interbeat intervals for recording
        self.ibiRecord = []
        
        #pointer to the recording list
        self.idx = 0
        
        #time of the next scheduled beat
        self.tNextBeat = -1
        
        self.percentage = 1.0
        
        
    #prepare for a new experimental run    
    def newRun(self,t,percentage):
        
        #empty the beat timestamp list
        self.beats = []
        
        #if the recording list is not empty
        if len(self.ibiRecord)>0:
            
            #copy the recording list to the reading list
            self.ibiRead = self.ibiRecord

        #empty the recording
        self.ibiRecord = []
   
        #reset the recording index
        self.idx = 0
        
        if percentage > 0: 
            self.percentage = 100.0 / percentage
        else:
            self.percentage = 1
            
        
        #schedule the onset of the next beat
        self.scheduleNextBeat(t)
        
        
        
    #PLAY: method for scheduling onset of next beat
    def scheduleNextBeat(self,t):
    
        #next beat is current time plus ibi
        self.tNextBeat = t + ( self.ibiRead[self.idx] * self.percentage )
        
        #raise the ibi index
        self.idx += 1
        
        #if end is reached start again from the beginning
        if self.idx + 1 > len(self.ibiRead):
        
            self.idx = 0
            
        
    #RECORD: add a heartbeat timestamp 
    def addBeat(self,t):
            
        #add beat timestamp to the end of the list        
        self.beats.append(t)
        
        #if at least two values in the list
        if len(self.beats) >= 2:
            
            #if more than two values in the list
            while len(self.beats) != 2:
                
                #successively remove first entries from the list until only 2 are left
                self.beats.pop(0)
           
            #then calculate the difference between the remaining beat timestamps
            val = self.beats[1] - self.beats[0]
            
            #check if value within reasonable limits
            if val > 0.2 and val < 2.0:
            
                #add the value to the record list
                self.ibiRecord.append(val)
            
    
    #read the next interbeat interval
    def getBeat(self,t):
        
        if (self.tNextBeat > 0 ) and ( t - self.tNextBeat >= 0 ) and ( t - self.tNextBeat <= 0.300 ):
            
            return True
            
        else:
        
            return False

# ======== End of Replay Buffer class ==================================================


#components used
self.ecg = self.controller.gModuleList['ecg']
self.imgLeft = self.controller.gModuleList['imgLeft']
self.imgRight = self.controller.gModuleList['imgRight']

#runtime variables left stim
self.onTimeLeft = 0.0
self.stimDurLeft = 0.5
self.stimOnLeft = 0

#runtime variables right stim
self.onTimeRight = 0.0
self.stimDurRight = 0.5
self.stimOnRight = 0

#number of trial
self.numTrial = 0

#make an asynchronous stimulus scheduling object
self.asynch = ReplayBuffer()

#percent duration of the original interbeat interval 
self.asynchPercent = 100.0

#prepare output logging
now = datetime.today()
self.csvLogger = csv.writer(open(path.join(self.controller.gLogger.Path, now.strftime('%y%m%d%H%M%S_') + self.initConf['name'] +  '.csv') , 'w'), lineterminator = '\n')
hdr = ['time','trial','percentAsynch','beatSynch','beatAsynch','stimLeft','stimRight']
self.csvLogger.writerow(hdr)