'''
Communicate with real-time BCI system

@author: Nathan
@since: Spring 2011

'''

from os import path
import numpy as np
import csv
import math
from datetime import datetime
from pyglet.gl import *

#pylnco modules
from abstract.AbstractClasses import SourceModule
from tracker.BCInterfaceHandler import BCIHandler
from controller import getPathFromString


class ModuleMain(SourceModule):
    """
    Interface between EXPYVR and . Interacts over UDP to interpret BCI commands and 
    feed different components what they want.
    """
    
    defaultInitConf = {
        'name': 'bci',
        'udpPort': 8989,
        'updateFrequency': 100
    }
    
    defaultRunConf = {
    }
    
    confDescription = [
        ('name', 'str', "Stroke Robot End Effector"),
        ('udpPort', 'int', "Port for UDP communication"),
        ('updateFrequency', 'float', "Frequency (in Hz) to retrieve the sensor data")
    ]
    
    def __init__(self, controller, initConfig=None, runConfigs=None):
        SourceModule.__init__(self, controller, initConfig, runConfigs)
                
        #Init network interface
        self.bciInterface = BCIHandler(self.initConf['udpPort'], "eth0")
        self.bciInterface.start()
        
        self.updateInterval = 1./self.initConf['updateFrequency']
        self.curDecision = 0
                                
    def start(self, dt=0, duration=-1, configName=None):
        SourceModule.start(self, dt, configName)        
        self._update(0)
        pyglet.clock.schedule_interval(self._update, self.updateInterval)

    def stop(self, dt=0):
        SourceModule.stop(self, dt)
        pyglet.clock.unschedule(self._update)
        
    def cleanup(self):
        SourceModule.cleanup(self)        
        self.bciInterface.stop()
        self.bciInterface.disconnect()
        
    def _update(self, dt):
        """
        Called at update frequency retrieve messages from BCI system
        """
        self.curDecision = self.bciInterface.getDecision()
        
        if(not self.curDecision == 0.0):
            self.log("d=" + str(self.curDecision))

    #Abstract methods for source modules 
    def getData(self):
        SourceModule.getData(self)
        return self.curDecision
            
    def getUpdateInterval(self):
        SourceModule.getUpdateInterval(self)
        return self.updateInterval