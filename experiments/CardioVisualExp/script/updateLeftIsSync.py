#current time
currTime = time()

#reset variables at first iteration
if self.starting:
    
    #raise the trial number
    self.numTrial+=1
    
    #both images to the back
    self.imgLeft.depth = -1.5
    self.imgRight.depth = -1.5
    
    #stimulus Left runtime variables
    self.onTimeLeft = 0.0
    self.stimOnLeft = 0
    
    #stimulus Right runtime variables
    self.onTimeRight = 0.0
    self.stimOnRight = 0
    
    #make new run for the asynch condition
    self.asynch.newRun(currTime,self.asynchPercent)

#Stimulus Left = Sync
if self.stimOnLeft == 0:
    if self.ecg.realHeartbeat:
        #record a new heartbeat
        self.asynch.addBeat(currTime)
        self.onTimeLeft = currTime
        self.stimOnLeft = 1
        self.imgLeft.depth = 1.5
        line = [currTime,self.numTrial,self.asynchPercent,1,0,1,0]
        self.csvLogger.writerow(line)     
else:
    if time()-self.onTimeLeft > self.stimDurLeft:
        self.stimOnLeft = 0
        self.imgLeft.depth = -1.5
    
    
#Stimulus Right = Async
if self.stimOnRight == 0:
    if self.asynch.getBeat(currTime):
        #schedule next asynch beat
        self.asynch.scheduleNextBeat(currTime)
        self.onTimeRight = currTime
        self.stimOnRight = 1
        self.imgRight.depth = 1.5
        line = [currTime,self.numTrial,self.asynchPercent,0,1,0,1]
        self.csvLogger.writerow(line)  
else:
    if time()-self.onTimeRight > self.stimDurRight:
        self.stimOnRight = 0
        self.imgRight.depth = -1.5
