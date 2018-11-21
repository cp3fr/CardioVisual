

class BufferBox(object):
    
    def __init__(self, duration, n = 10):
        # Default exponential moving average alpha coeficient for 10 values decay
        self.EMA_alpha = 2.0 / (n + 1.0)
        self.max_duration = long((duration + 1) * 1000000.0)
        self.valuestack = {}
        self.orderedkeys = []
        self.valueaverage = 0.0
        
    def appendValue(self, time, value):
        # add the value to the buffer
        keytime = long(time * 1000000.0)
        self.valuestack[keytime] = value
        # keep set or keys ordered by time
        self.orderedkeys.append(keytime)
        # make sure time order is kept in array of keys (should never happen than a value is given with past time)
        if (len(self.orderedkeys) > 2) and (self.orderedkeys[-1] < self.orderedkeys[-2]):
            self.orderedkeys = sorted(self.orderedkeys)
            
        # remove every values earlier than max_duration ago 
        while self.orderedkeys[0] < (keytime - self.max_duration):
            if self.valuestack.has_key(self.orderedkeys[0]):
                self.valuestack.pop(self.orderedkeys[0])
                self.orderedkeys.pop(0)
            
        # estimate exponential moving average of value
        if len(self.valuestack) < 2:
            self.valueaverage = value
        else:
            self.valueaverage = self.EMA_alpha * value + (1.0 - self.EMA_alpha) * self.valueaverage

    def getValue(self, time = None):        
        if len(self.valuestack)<1:
            return 0.0;
        # if no time is given or only one elements in the buffer
        # return the last element
        if (time is None) or (len(self.orderedkeys) < 2):
            return self.valuestack[self.orderedkeys[-1]]
        # if the time given is in the future 
        # return the last element
        keytime = long(time * 1000000.0)
        if (keytime > self.orderedkeys[-1]):
            return self.valuestack[self.orderedkeys[-1]]
        # if time given is before the first value, return the first value
        if (keytime < self.orderedkeys[0]):
            return self.valuestack[self.orderedkeys[0]]
        # maybe lucky to have the exact key
        if self.orderedkeys.count(keytime):
            return self.valuestack[keytime]
        # otherwise find the time asked between the past key times
        low_keytime = keytime
        while self.orderedkeys.count(low_keytime) < 1:
            low_keytime -= 1
        # get the next key time
        high_keytime = self.orderedkeys[self.orderedkeys.index(low_keytime)+1]
        # linear interpolation
        div = high_keytime - low_keytime
        if div > 0:
            return self.valuestack[low_keytime] + float(keytime - low_keytime) * float( self.valuestack[high_keytime] -self.valuestack[low_keytime] ) / float(div) 
        else:
            return self.valuestack[high_keytime]
            
    def getAverage(self):
        if len(self.valuestack) < 1:
            return 0.0;
        """
        if len(self.valuestack) < 10:
            return self.valuestack[self.orderedkeys[-1]]
        """
        return self.valueaverage
        
    def getLength(self):
        return len(self.valuestack)
        
    def reset(self):
        self.valuestack = {}
        self.orderedkeys = []
        self.valueaverage = 0.0
        
    def getDuration(self):
        return float(self.max_duration)/1000000.0