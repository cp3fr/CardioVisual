#current time
currTime = time()

#--- Things to do on the first iteration -----------------------------------------------------

#if first iteration..
if self.starting:
    
    #..raise the trial number
    self.numTrial += 1
    
    #..switch both images to low alpha value
    self.imgLeft.alpha = self.alphaLow
    self.imgRight.alpha = self.alphaLow
    
    #..reset stimulus Left runtime variables
    self.onTimeLeft = 0.0
    self.stimOnLeft = False
    
    #..stimulus Right runtime variables
    self.onTimeRight = 0.0
    self.stimOnRight = False
    
    #..switch to next run in the buffer object
    self.buffer.newRun(currTime,self.asynchPercent)
    
    #..set the time of the next simulated beat
    self.simNextBeat = currTime + self.simISI

    
#set the picture stimuli according to randomization info   
self.imgLeft.index = self.rand[self.numTrial][0]
self.imgRight.index = self.rand[self.numTrial][1]
    

#--- Sim Mode or Real Heartbat Recording ? -------------------------------------------------------

#if in sim mode..
if self.simMode:

    #..check if time has come for next simulated beat
    if self.simNextBeat - currTime < 0:
    
        #set real beat to true
        self.buffer.setRealBeat(True)
        
        #schedule next simulated beat
        self.simNextBeat = currTime + self.simISI
        
    #if no simulated beat time    
    else:
        
        #set real beat to off
        self.buffer.setRealBeat(False)
    
#if not in sim mode..
else:

    #set real beat according to ecg module reading
    self.buffer.setRealBeat(self.ecg.realHeartbeat)

    
#--- Left Stimulus Scheduling ----------------------------------------------------------------
 
#if stimulus is off..
if not self.stimOnLeft:

    #..check if SYNCH mode required and whether there is a synch heartbeat..
    if ( self.rand[self.numTrial][2] == 1.0 ) and ( self.buffer.getRealBeat() ):
    
        #..set stimulus to high alpha
        self.imgLeft.alpha = self.alphaHigh  
        
        #..flag stimulus as on
        self.stimOnLeft = True
    
        #..save stimlus on time
        self.onTimeLeft = currTime
    
        #..record current time of real heartbeat to buffer
        self.buffer.addBeat(currTime)
        
    #..check if ASYNCH mode is required and whether there is a asynch heartbeat..
    elif ( self.rand[self.numTrial][2] == 0.0 ) and ( self.buffer.getBeat(currTime) ):
    
        #..set stimulus to high alpha
        self.imgLeft.alpha = self.alphaHigh  
        
        #..flag stimulus as on
        self.stimOnLeft = True
    
        #..save stimlus on time
        self.onTimeLeft = currTime
    
        #..schedule next asynch beat
        self.buffer.scheduleNextBeat(currTime)

#if stimulus is on..        
else:

    #..check if stimulus on time has passed..
    if time()-self.onTimeLeft > self.stimOnDuration:
    
        #..set stimlus to low alpha
        self.imgLeft.alpha = self.alphaLow
        
        #..flag stimlus as off
        self.stimOnLeft = False
        
   
#--- Right Stimulus Scheduling ----------------------------------------------------------------
 
#if stimulus is off..
if not self.stimOnRight:

    #..check if SYNCH mode required and whether there is a synch heartbeat..
    if ( self.rand[self.numTrial][3] == 1.0 ) and ( self.buffer.getRealBeat() ):
    
        #..set stimulus to high alpha
        self.imgRight.alpha = self.alphaHigh  
        
        #..flag stimulus as on
        self.stimOnRight = True
    
        #..save stimlus on time
        self.onTimeRight = currTime
    
        #..record current time of real heartbeat to buffer
        self.buffer.addBeat(currTime)
        
    #..check if ASYNCH mode is required and whether there is a asynch heartbeat..
    elif ( self.rand[self.numTrial][3] == 0.0 ) and ( self.buffer.getBeat(currTime) ):
    
        #..set stimulus to high alpha
        self.imgRight.alpha = self.alphaHigh  
        
        #..flag stimulus as on
        self.stimOnRight = True
    
        #..save stimlus on time
        self.onTimeRight = currTime
    
        #..schedule next asynch beat
        self.buffer.scheduleNextBeat(currTime)

#if stimulus is on..        
else:

    #..check if stimulus on time has passed..
    if time()-self.onTimeRight > self.stimOnDuration:
    
        #..set stimlus to low alpha
        self.imgRight.alpha = self.alphaLow
        
        #..flag stimlus as off
        self.stimOnRight = False
        
        
#--- Logging -------------------------------------------------------------------------------------

#if real or asynch beat..
if self.buffer.getRealBeat() or self.buffer.getBeat(currTime):

    #..prepare logline
    line = [currTime,
            self.numTrial + 1, #because counting starts with zero
            self.asynchPercent,
            self.buffer.getRealBeat(),
            self.buffer.getBeat(currTime),
            self.stimOnLeft,
            self.stimOnRight,
            self.rand[self.numTrial][0],
            self.rand[self.numTrial][1]
            ]
     
    #..write logline to file     
    self.csvLogger.writerow(line)       