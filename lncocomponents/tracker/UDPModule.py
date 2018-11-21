'''
Communicate with real-time UDP system

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
#from abstract.AbstractClasses import SourceModule
from abstract.AbstractClasses import DrawableHUDSourceModule
from tracker.UDPInterfaceHandler import UDPHandler
from controller import getPathFromString
        
#class ModuleMain(SourceModule):
class ModuleMain(DrawableHUDSourceModule):
    """
    Interface between EXPYVR and peripherals such as robots or BCIs based on UDP. It interacts over UDP to interpret UDP commands and 
    feed different components what they want.
    IF YOU WANT TO CONFIGURE THE UDP FOR A NOVEL DEVICE: add the name in the configuration options (line 45 of UDPModule.py),
    and then open UDPInterfaceHandler.py and add a new case in the if-elif options within the handle function that you will find at the bottom of the file (starting line 135)
    """
    curPacket = 0

    
    defaultInitConf = {
        'name': 'udp_handler',
        'udpPort': 8989,
        'updateFrequency': 100,
        'config': "printonscreen",
    }
    
    defaultRunConf = {
    }
    
    confDescription = [
        ('name', 'str', "Stroke Robot End Effector"),
        ('udpPort', 'int', "Port for UDP communication"),
        ('updateFrequency', 'float', "Frequency (in Hz) to retrieve the sensor data"),
        ('config', 'str', "data handling (depends on the device)", ['printonscreen', 'two_finger_bot','BCI_reader','stroke_bot']),
        #IF YOU WANT TO CONFIGURE THE UDP FOR A NOVEL DEVICE: add the name in the upper line, and then open UDPInterfaceHandler.py 
        # and add a new case in the switch in the handle function that you will find at the bottom of the file
        
    ]
    
    def __init__(self, controller, initConfig=None, runConfigs=None):
        #SourceModule.__init__(self, controller, initConfig, runConfigs)
        DrawableHUDSourceModule.__init__(self, controller, initConfig, runConfigs)
        self.label = None 

        #Init network interface
        self.udpInterface = UDPHandler(self.initConf['udpPort'], "eth0")
        self.udpInterface.start(self.initConf['config'])
        
        self.updateInterval = 1./self.initConf['updateFrequency']
        self.curPacket = 0

    def draw(self, window_width, window_height, eye=-1):
        DrawableHUDSourceModule.draw(self, window_width, window_height)

        if self.label is None:
            self.label = pyglet.text.Label(text='',
                                       color=(255, 0, 0, 255),
                                       font_name='arial',
                                       font_size=20,
                                       anchor_x='left', anchor_y='center',
                                       width=600, multiline=False,
                                       x=100, y=100)
        if (self.initConf['config']=='printonscreen'):
            self.label.text = ' data : %s'%(  str(self.curPacket) )
            self.label.draw() 
        
    def start(self, dt=0, duration=-1, configName=None):
        #SourceModule.start(self, dt, configName)        
        DrawableHUDSourceModule.start(self, dt, configName)
        pyglet.clock.schedule_interval(self._update, self.updateInterval)
        
    def stop(self, dt=0):
        #SourceModule.stop(self, dt)
        DrawableHUDSourceModule.stop(self, dt)
        pyglet.clock.unschedule(self._update)
        
    def cleanup(self):
        #SourceModule.cleanup(self)        
        DrawableHUDSourceModule.cleanup(self) 
        
        self.udpInterface.stop()
        self.udpInterface.disconnect()
        
    def _update(self, dt):
        """
        Called at update frequency retrieve messages from UDP system
        """
        
        self.curPacket = self.udpInterface.getPacket()


    #Abstract methods for source modules 
    def getData(self):
        #SourceModule.getData(self)
        DrawableHUDSourceModule.getData(self) 
        return self.curPacket
            
    def getUpdateInterval(self):
        #SourceModule.getUpdateInterval(self)
        DrawableHUDSourceModule.getUpdateInterval(self)
        return self.updateInterval