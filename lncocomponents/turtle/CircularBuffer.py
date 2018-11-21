#CircularBuffer class creates a data buffer object that updates efficiently by operating element-wise instead of shifting a whole array. It also computes element-wise differences and allows to extract average values 
class CircularBuffer(object):

    #initialization of class member variables
    def __init__(self, size):
        self.index= 0 #pointer to buffer position
        self.size= size
        self.data = []
        self.diff = []

    def addVal(self, value):
        #if buffer full: update element-wise using the index pointer and update difference vector
        if len(self.data) >= self.size:
            #update data buffer
            self.data[self.index]= value
            #update data difference buffer
            if self.index > 0:
                self.diff[self.index-1]=abs(self.data[self.index]-self.data[self.index-1])
        #if buffer not full: append input values
        else:
            #just append data
            self.data.append(value)
            #and append difference between subsequent values
            n=len(self.data)-1
            if n>0:
                self.diff.append(abs(self.data[n]-self.data[n-1]))
        #update data pointer
        self.index= (self.index + 1) % self.size
        if self.index > self.size:
            self.index = 0
                
    def getVal(self, key):
        return(self.data[key])

    def getAll(self):
        return(self.data)

    def getAverage(self):
        if len(self.data)>0:
            return(sum(self.data) / len(self.data))
        else:
            return []
        
    def getDiff(self):
        return(self.diff)
    
    def getDiffAverage(self):
        #note that absolute values are used as we are not interested in direction
        if len(self.diff)>0:
            return(sum(self.diff) / len(self.diff))
        else:
            return []