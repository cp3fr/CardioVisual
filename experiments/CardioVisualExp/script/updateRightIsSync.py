#reset variables at first iteration
if self.starting:
    #stimulus Left runtime variables
    self.onTimeLeft = 0.0
    self.stimOnLeft = 0
    #stimulus Right runtime variables
    self.onTimeRight = 0.0
    self.stimOnRight = 0

   
#Stimulus Left = Async
if self.stimOnLeft == 0:
    if self.ecg.beat == 1:
        self.onTimeLeft = time()
        self.stimOnLeft = 1
        self.imgLeft.depth = 1.5
else:
    if time()-self.onTimeLeft > self.stimDurLeft:
        self.stimOnLeft = 0
        self.imgLeft.depth = -1.5
    
    
#Stimulus Right = Sync
if self.stimOnRight == 0:
    if self.ecg.realHeartbeat == 1:
        self.onTimeRight = time()
        self.stimOnRight = 1
        self.imgRight.depth = 1.5
else:
    if time()-self.onTimeRight > self.stimDurRight:
        self.stimOnRight = 0
        self.imgRight.depth = -1.5
    