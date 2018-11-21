'''
Created on Jan 29, 2011

@author: bh
@since: winter 2010

@license: Distributed under the terms of the GNU General Public License (GPL).
'''

from os import path
import csv, copy
import threading, time
import socket, re

from datetime import datetime
from pyglet.gl import *
import numpy as np

#pylnco modules
from display.tools import *
from abstract.AbstractClasses import DrawableHUDSourceModule
from display.objloader import OBJ
from controller import getPathFromString
from pyglet.clock import _default_time_function as time

#NI-DAQmx library
from tracker.PyDAQmx import *
from numpy import *

class ModuleMain(DrawableHUDSourceModule):

    defaultInitConf = {
        'name': 'NiDAQmx',
        'logToCSV': True,
    }
    
    defaultRunConf = {
        'volts': 0.0,
    }
    
    confDescription = [
        ('name', 'str', "National Instruments DAQmx module."),
        ('logToCSV', 'bool', "Save data to coma-separated-values file (<modulename>_<date>.csv)"),
        ('volts', 'float', "Volts to output."),
        ('setVolts()', 'info', "Set volts to output (float) in real-time using the script module."),
    ]
    
    def __init__(self, controller, initConfig=None, runConfigs=None):
        DrawableHUDSourceModule.__init__(self, controller, initConfig, runConfigs)
        
        self.task = Task()
        self.task.CreateAOVoltageChan("Dev1/ao0", "", 0.0, 10.0, DAQmx_Val_Volts, "")
        self.data = array(0.0)
        self.volts = 0.0
        self.label = None
        
        # Initialize logger 
        self.logActive = self.initConf['logToCSV']
        now = datetime.today()
        if self.logActive:
            self.csvLogger = csv.writer(open(path.join(self.controller.gLogger.Path, now.strftime('%y%m%d%H%M%S_') + self.initConf['name'] +  '.csv') , 'w'), lineterminator = '\n')
            line = ['exp_time', 'Routine', 'Condition', 'volts']
            self.csvLogger.writerow(line)
        
    def start(self, dt=0, duration=-1, configName=None):
        DrawableHUDSourceModule.start(self, dt, duration, configName)
        
        self.volts = self.activeConf['volts']
        self.data = array(self.volts)
        
        self.task.StartTask()
        self.task.WriteAnalogF64(1, 1, 10.0, DAQmx_Val_GroupByChannel, self.data, None, None)
        
        # Fill in logs if required
        if self.logActive:
            # Log time
            line = [str("%.4f"%self.controller.gTimeManager.experimentTime()), self.controller._currentRoutine, self.controller._currentCondition]
            # Log info
            line.extend([self.volts])
            self.csvLogger.writerow(line)
        
        pyglet.clock.schedule(self.update)
        
    def stop(self, dt=0):
        DrawableHUDSourceModule.stop(self, dt)
        pyglet.clock.unschedule(self.update)
        
        self.task.WriteAnalogF64(1, 1, 10.0, DAQmx_Val_GroupByChannel, zeros(1), None, None)
        self.task.StopTask()
        
    def cleanup(self):
        DrawableHUDSourceModule.cleanup(self)
        pyglet.clock.unschedule(self.update)
        
        self.task.ClearTask()
        
    def setVolts(self, volts):
        self.volts = volts
        self.data = array(self.volts)
        
        if (self.volts > 0.0):
            self.task.WriteAnalogF64(1, 1, 10.0, DAQmx_Val_GroupByChannel, self.data, None, None)
        else:
            self.task.WriteAnalogF64(1, 1, 10.0, DAQmx_Val_GroupByChannel, zeros(1), None, None)
        
        # Fill in logs if required
        if self.logActive:
            # Log time
            line = [str("%.4f"%self.controller.gTimeManager.experimentTime()), self.controller._currentRoutine, self.controller._currentCondition]
            # Log info
            line.extend([self.volts])
            self.csvLogger.writerow(line)
        
    def update(self, dt):
        pass
     
    def draw(self, window_width, window_height):
        DrawableHUDSourceModule.draw(self, window_width, window_height)

        if self.label is None:
            self.label = pyglet.text.Label(text='',
                                       color=(255, 0, 0, 255),
                                       font_name='arial',
                                       font_size=20,
                                       anchor_x='left', anchor_y='center',
                                       width=600, multiline=False,
                                       x=100, y=100)
        self.label.text = str("%.1f"%self.volts)
        self.label.draw()  