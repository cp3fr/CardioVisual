#import libraries
import csv
import re
from os import path
from time import time
from controller import getPathFromString


#--- Settings to be done by hand --------------------------------------------------------

#Whether to simulate heartbeats
self.simMode = True

#Interbeat intervals for [synch, asynch] conditions during simulation mode
self.simISI = 1.0

#percent duration of the original interbeat interval 
self.asynchPercent = 120.0

#alpha values for glow effect
self.alphaLow = 0.5
self.alphaHigh = 1.0

#on time of stimulus after beat detected
self.stimOnDuration = 0.2

#-------------------------------------------------------------------------------------------

#if not in sim mode, connect to the ECG module
if not self.simMode:
    self.ecg = self.controller.gModuleList['ecg']
    
#connect to modules for left and right image presentation
self.imgLeft = self.controller.gModuleList['ImageListLeft']
self.imgRight = self.controller.gModuleList['ImageListRight']

#set default image indices
self.imgLeft.index = 0.0
self.imgRight.index = 0.0

#runtime variables left stim
self.onTimeLeft = 0.0
self.stimOnLeft = False

#runtime variables right stim
self.onTimeRight = 0.0
self.stimOnRight = False

#number of trial
self.numTrial = -1

#time of the next beat
self.simNextBeat = -1

#prepare output logging
now = datetime.today()
self.csvLogger = csv.writer(open(path.join(self.controller.gLogger.Path, now.strftime('%y%m%d%H%M%S_') + self.initConf['name'] +  '.csv') , 'w'), lineterminator = '\n')
hdr = ['time','trial','percentAsynch','beatSynch','beatAsynch','stimLeft','stimRight','stimLeftIndex','stimRightIndex']
self.csvLogger.writerow(hdr)


#---Start of Replay Buffer Class---------------------------------------------------
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
        
        #real heartbeat
        self.realBeat = False
        
        
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
        
        self.realBeat = False
        
        
        
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
            
    #set the real heartbeat
    def setRealBeat(self,val):
        self.realBeat = val
        
        
    #get the real heartbeat
    def getRealBeat(self):
        return self.realBeat
      
#---End of Replay Buffer Class---------------------------------------------------       
    
#create object of the ReplayBuffer class, responsible for recording heartbeats and scheduling
#asynch heartbeats on the following trial
#the object also takes a copy of the real heartbeat and gives it back when desired
self.buffer = ReplayBuffer()

#load randomization information from text file
f = open(getPathFromString('$EXPYVRROOT$/experiments/CardioVisualExp/rand.txt'), 'r')

#regular expression to match
regexp = re.compile('([-+]?\d*)[,]([-+]?\d*)[,]([-+]?\d*)[,]([-+]?\d*)')

#empty randomization file
self.rand = []

#loop over lines
for line in f:
    
    #retrieve values by regular expression matching
    vals = regexp.match(line)

    #if a match was found..
    if vals is not None:
    
        #...add data to randomization file
        self.rand.append([float(vals.group(1)), float(vals.group(2)),float(vals.group(3)), float(vals.group(4))])

#close the file
f.close()

print('----- RAND FILE INFO ------------')

for line in self.rand:
    print(line)
