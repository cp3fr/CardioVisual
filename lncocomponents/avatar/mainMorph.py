'''
Load and iterate through morph animations for Avatars.

@author: Nathan, Tobias Leugger
@since: Spring 2011
'''

from pyglet.gl import *
from ctypes import *
import math
import numpy as np
import tracker #for source type

from abstract.AbstractClasses import BasicModule


class ModuleMain(BasicModule):
    defaultInitConf = {
        'name': 'morphAnim',
        'avatarName': 'avatar',        # name of module to animate
        'winSize': 64                   # window size in time frames to average classification output
    }
    
    defaultRunConf = {
        'morphAnimID': 0,           # ID of morph animation
        'gainSource': '',           # external component source for modulating gain of animation
        'removeOffset': 'none',     # remove DC offset of data input or not
        'mappingType': 'direct',    # specify mapping type
        'animThresh': 1,          # amount animation before changing direction (0 = no oscillation -> 1 (oscillate after full animation))
        'startPos': 0.0,            # where to start in animation (0->1)
        'animSpeed': 1              # in hz
    }
    
    confDescription = [
       ('name', 'str', "Morph Animation"),
       ('avatarName', 'str', "Name of avatar module to animate"),
       ('winSize', 'int', "Window size (in time frames - assumes SRATE = 128) to average classification over (used in smoothdirect mapping)"),       
       ('morphAnimID', 'int', "Morph animation ID to use (from avatar.cfg, starting with 0)"),       
       ('gainSource', 'str', "Animation source (empty if controlled by pre-rec animID; otherwise name of external component regulating gain)"),
       ('removeOffset', 'str', "Center source data around 0 (remove DC offset)",['none','mean','midmeans']),
       ('mappingType', 'str', "Extra option to specify how to map gain to animation. Must be coded in mainMorph.py",['direct','smoothdirect','increment','weightedincr']),
       ('animThresh', 'float', "Amount of animation before switching animation direction. 0 = no oscillation -> 1 (full animation)"),
       ('startPos', 'float', "Where to start in animation (between 0=beginning, 1=end)"),
       ('animSpeed', 'float', "Speed of animation in Hz for fully played animations. (EG: 1 = full animation executed once per second"),
   ]
        
    
    def __init__(self, controller, initConfig=None, runConfigs=None):
        BasicModule.__init__(self, controller, initConfig, runConfigs)
        
        # Get Avatar + library 
        try:
            self.HALCA = self.controller.gModuleList['avatarlib']
            self._avatarID = self.controller.gModuleList[self.initConf['avatarName']].avatar
        except:
            raise RuntimeError("Couldn't get avatar/library. Ensure avatar component is before morph animation.")

        # Add morph anims to library
        for conf in self.runConfs.values():
            self.HALCA.addMorph(self._avatarID, conf['morphAnimID'])
            
        #init
        self._curMorphID = -1
        self._pctAnimated = 0.0
        self._animDir = 1
        self._source = None        
        self._bciAnim = BCIAnimation(self.initConf['winSize']) #in case we're using special BCI type mapping
        
        
                                             
    def start(self, dt=0, duration=-1, configName=None):
        """
        Activate with the parameters passed in the conf
        """
        BasicModule.start(self, dt, duration, configName)
        self._resetAnimation()

        if(self.activeConf["gainSource"] == ''):
            totalNF = self.HALCA.getAnimationNumFrames(self._avatarID, self._curMorphID)
            totalDur = self.HALCA.getAnimationDuration(self._avatarID, self._curMorphID)
            frate = (totalDur / totalNF) / totalDur        
        else:
            self._source = self.controller.gModuleList[self.activeConf['gainSource']]
            print "Source set: " + str(self._source)
            frate = self._source.getUpdateInterval()
                        
        pyglet.clock.schedule_interval(self._update, frate)
        

    def stop(self, dt=0):
        BasicModule.stop(self, dt)
        self._resetAnimation()
        
    def cleanup(self):
        BasicModule.cleanup(self)
         

    def _update(self,dt=0):
        sType = str(self._source.__class__)

        #Handle different source <-> animation couplings
        if(sType == 'BCIModule.ModuleMain'):
            self._mapFeedback(self.activeConf['mappingType'],self.activeConf['removeOffset'])
            
        else:
            #Default: Increment animation one step closer to goal (oscillate if threshold specified)
            T = self.activeConf['animThresh']
            totalNF = self.HALCA.getAnimationNumFrames(self._avatarID, self._curMorphID)
            totalDur = self.HALCA.getAnimationDuration(self._avatarID, self._curMorphID)        
            STEPSIZE = ((totalDur / totalNF) / totalDur)  #take % of frames to increment (normalized [0-1))         
            STEPSIZE = (STEPSIZE * totalDur * self.activeConf['animSpeed'])
                            
            #Test if we should reverse direction
            if(T > 0 and self._pctAnimated >= T):
                self._animDir = -1            
            elif(self._animDir == -1 and self._pctAnimated <= 0):   #from negative
                self._animDir = 1
            else:                                                   #catch case (if treshold/start pos is set errantly)
                self._animDir = 1
            
            self.HALCA.incMorph(self._avatarID, self._curMorphID, self._animDir*STEPSIZE)
                    
            #Increment frame
            if self._animDir > 0:
                self._pctAnimated += STEPSIZE
            else:
                self._pctAnimated -= STEPSIZE


        self.HALCA.Idle(None)
        
    def _mapFeedback(self,mapType,offType):
        curDecision = self._bciAnim.update(self._source.getData(),mapType,offType)

        if mapType == 'direct' or mapType == 'smoothdirect':
            # Take BCI classification values (usually ranging [-1 1]), directly update animation
            # left hand if value < 0 (morph animation 0); right hand if value > 0 (morph animation 1) 
            if(curDecision < 0):
                if curDecision < -1:        #cap at hand clasp
                    curDecision = -1
                self.HALCA.setMorph(self._avatarID, 0, math.fabs(curDecision))  #left hand
            else:
                if curDecision > 1:        #cap at hand clasp
                    curDecision = 1
                self.HALCA.setMorph(self._avatarID, 1, math.fabs(curDecision))  #right hand
                    
        elif mapType == 'increment' or 'weightedincr':
            totalNF = self.HALCA.getAnimationNumFrames(self._avatarID, self._curMorphID)
            totalDur = self.HALCA.getAnimationDuration(self._avatarID, self._curMorphID)
            STEPSIZE = 0.001 #totalDur / totalNF               #take % of frames to increment (normalized [0-1))         
                            
            if mapType == 'weightedincr':
                #rescale STEPSIZE to magnitude of curDecision - mapping handled in BCIAnim
                STEPSIZE = 0.001 + curDecision/500 #(totalDur / totalNF) + curDecision                    
            
#            #Test if we should reverse direction
#            if(T > 0 and self._pctAnimated >= T):
#                self._animDir = -1            
#            elif(self._animDir == -1 and self._pctAnimated <= 0):   #from negative
#                self._animDir = 1
#            else:                                                   #catch case (if treshold/start pos is set errantly)
#                self._animDir = 1
            
            if(curDecision < 0):
                self.HALCA.incMorph(self._avatarID, 0, self._animDir*STEPSIZE)  #left hand
            elif(curDecision > 0):
                self.HALCA.incMorph(self._avatarID, 1, self._animDir*STEPSIZE)  #right hand                                
                    
#            #Increment frame
#            if self._animDir > 0:
#                self._pctAnimated += STEPSIZE
#            else:
#                self._pctAnimated -= STEPSIZE
                
        

    def _resetAnimation(self):        
        self._pctAnimated = 0.0
        self._animDir = 1
        
        self.HALCA.Idle(None)
        self._curMorphID = self.activeConf['morphAnimID']
        self.HALCA.setMorph(self._avatarID, self._curMorphID, self.activeConf['startPos'])

    def setMorphAnimation(self,avaID,animID,startPos):
        """
        Allow outside intervention of the current animation ID
        """
        self.HALCA.setMorph(avaID, animID, startPos)
    

class BCIAnimation():
    def __init__(self,wSize):
        self.winSize = wSize
        self.lbIdx = 0
        self.lowBuffer = np.zeros(wSize)
        self.hbIdx = 0
        self.highBuffer = np.zeros(wSize)
        
        self.avgmin = float('inf')
        self.avgmax = -float('inf')
        
        self.fullmean = 0.0           #mean of all data coming in from classifier
        self.highmean = 0.0
        self.lowmean = 0.0            #keep a mean classification output val for those less than 0
        
        self.numHigh = 0            #counter for how many 'low' (left/right) commands were sent
        self.numLow = 0             #count how many 'high' (right/left) commands sent
    
    
    def update(self,data,mType,oType):
        #Update running statistics with new data point
        numSamples = self.numHigh + self.numLow + 1
        self.fullmean = self.fullmean + (data - self.fullmean)/(numSamples)

        if(data > 0):
            self.numHigh = self.numHigh + 1
            self.highmean = self.highmean + (data - self.highmean)/(self.numHigh)
        else:
            self.numLow = self.numLow + 1
            self.lowmean = self.lowmean + (data - self.lowmean)/(self.numLow)

        
        # Return updated decision value according to mapping type        
        if mType == 'direct':
            newValue = data
        
        elif mType == 'smoothdirect':
            if(data < 0):            
                self.lowBuffer[self.lbIdx] = data                   #add to ring buffer
                self.lbIdx = np.mod(self.lbIdx+1,self.winSize)    #update buffer index
                newValue = np.mean(self.lowBuffer)                 #take mean on buffer
            elif(data > 0):
                self.highBuffer[self.hbIdx] = data                   #add to ring buffer
                self.hbIdx = np.mod(self.hbIdx+1,self.winSize)    #update buffer index
                newValue = np.mean(self.highBuffer)                 #take mean on buffer
            else:
                newValue = data

        elif mType == 'increment':
            newValue = data
            
        elif mType == 'weightedincr':
            if(data < 0):
                newValue = -1*(data/self.lowmean)        #percent increase over mean
            elif(data > 0):
                newValue = data/self.highmean
            else:
                newValue = 0
        else:
            newValue = data
                 
        # DC center
        if oType == 'mean':
            newValue = newValue - self.fullmean
        elif oType == 'midmeans':
            newValue = newValue - ((self.highmean-self.lowmean)/2)

        return newValue