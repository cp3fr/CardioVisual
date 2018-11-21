# import libraries
import re
from controller import getPathFromString
import random as random

#Randomization, reads trial specification parameters from a randomization file, each row should contain comma separated double values, the number of 
class Randomization(object):

    #initialize by giving a path to the randomization file
    def __init__(self, dict, shuffle=True):
        
        #output list storing trial specification values
        self.outVals = []
        
        #extract keys and values from the input dictionairy
        self.keys = [] #save this one for making trial dictionaires
        vals = []
        lens = []
        for key,val in dict.items():
            self.keys.append(key)
            vals.append(dict[key])
            lens.append(len(dict[key]))
        
        #combine all possible condition levels
        if len(lens) == 5:
            for i0 in range(lens[0]):
                for i1 in range(lens[1]):
                    for i2 in range(lens[2]):
                        for i3 in range(lens[3]):
                            for i4 in range(lens[4]):
                                #compose line by loop over all the entries
                                line = []
                                line.append(vals[0][i0])
                                line.append(vals[1][i1])
                                line.append(vals[2][i2])
                                line.append(vals[3][i3])
                                line.append(vals[4][i4])
                                #add line to output value list
                                self.outVals.append(line)
        else:
            raise('>> Error: Randomization dict has wrong number of entries.')
    
        #if shuffle desired apply three times
        if shuffle:
            self.shuffle()
            self.shuffle()
            self.shuffle()

    # return the trial values for the trial indexed by numtrial
    def get(self, numTrial):
        
        #make a dictionaire for the current trial
        trialDict = {}
        for i in range(len(self.keys)):
            trialDict[self.keys[i]] = self.outVals[numTrial][i]
        
        #return trial dictionaire
        return trialDict
        
    def getNumTrials(self):
        return len(self.outVals)
    
    def getKeys(self):
        return self.keys
     
    #shuffle the order of trials     
    def shuffle(self):
        self.outVals = random.sample(self.outVals, len(self.outVals))
        
    