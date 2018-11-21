

class BufferBox(object):
     # exponential moving average alpha coeficient for 10 values decay
    EMA_alpha = 2.0 / (10.0 + 1.0)
    
    def __init__(self, duration):
        self.reset()
        self.max_duration = long(duration * 1000.0)
        
    def appendValue(self, time, value):
        # add the value to the buffer
        keytime = long(time * 1000.0)
        self.valuestack[keytime] = value
        # remove every values earlier than max_duration ago 
        for i in sorted(self.valuestack.keys()):
            if i < keytime - self.max_duration:
                self.valuestack.pop(i)
            else:
                break
        # estimate exponential moving average of value
        if len(self.valuestack) < 2:
            self.valueaverage = value
        else:
            self.valueaverage = BufferBox.EMA_alpha * value + (1.0 - BufferBox.EMA_alpha) * self.valueaverage
        
    def getValue(self, time = None):        
        if len(self.valuestack)<1:
            return 0;
        orderedkeys = sorted(self.valuestack.keys())
        # if no time is given or only one elements in the buffer
        # return the last element
        if time is None or len(orderedkeys) < 2:
            return self.valuestack[orderedkeys[-1]]
        # if the time given is in the future 
        # return the last element
        keytime = long(time * 1000.0)
        if keytime > orderedkeys[-1]:
            return self.valuestack[orderedkeys[-1]]
        # if time given is before the first value, return the first value
        if keytime < orderedkeys[0]:
            return self.valuestack[orderedkeys[0]]
        # otherwise find the time asked in the past key times
        low_keytime = keytime
        while orderedkeys.count(low_keytime) < 1:
            low_keytime -= 1
        # get the next key time
        high_keytime = orderedkeys[orderedkeys.index(low_keytime)+1]
        # linear interpolation
        return self.valuestack[low_keytime] + float(keytime - low_keytime) * float( self.valuestack[high_keytime] -self.valuestack[low_keytime] ) / float (high_keytime - low_keytime)

    def getAverage(self):
        return self.valueaverage
        
    def getLength(self):
        return len(self.valuestack)
    
    def reset(self):
        self.max_duration = 1000
        self.valuestack = {}
        self.valueaverage = 0
