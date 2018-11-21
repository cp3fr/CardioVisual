'''
Parallel Port Input

To read status pins from parallel port

@author: Javier Bello
@since July 2012
'''

from os import path
import csv
from datetime import datetime
from pyglet.gl import *
from abstract.AbstractClasses import BasicModule
from pyglet.clock import _default_time_function as time

import controller.trigManager as tManager
from input.parallelPort import *

class ModuleMain(BasicModule):    
    defaultInitConf = {
        'name': 'ParallePortInput',
        'Data port address': '0x378',
        'Status port address': '0x379',
        'Control port address': '0x37A',
        'logToCSV': True
    }
    
    defaultRunConf = {
    }
        
    confDescription = [
       ('name', 'str', "Module for reading values from the parallel port."),
       ('Data port address', 'str', 'Parallel port address.'),
       ('Status port address', 'str', 'Parallel port address + 1'),
       ('Control port address', 'str', 'Parallel port address + 2'),
       ('logToCSV', 'bool', "Save integer values from the parallel port status pins in a Comma Separated Values text file."),
       ('getData()', 'info', "Read current integer value from the parallel port data pins."),
       ('getStatus()', 'info', "Read current integer value from the parallel port status pins."),
       ('getControl()', 'info', "Read current integer value from the parallel port control pins.")
   ]
    
    def __init__(self, controller, initConfig=None, runConfigs=None):
        BasicModule.__init__(self, controller, initConfig, runConfigs)
        
        # Start logger
        self.csvLogger = None
        if self.initConf['logToCSV']:
            now = datetime.today()
            self.csvLogger = csv.writer(open(path.join(self.controller.gLogger.Path, now.strftime('%y%m%d%H%M%S_') + self.initConf['name'] + '.csv'), 'w'), lineterminator = '\n')
            self.csvLogger.writerow(['expTime', 'routine', 'condition', 'dataCode', 'statusCode', 'controlCode'])

        self.dataAddress = self.initConf['Data port address']
        self.statusAddress = self.initConf['Status port address']
        self.controlAddress = self.initConf['Control port address']
        
        self.data = 255
        self.status = 255
        self.control = 255
        
        # Try to connect to parallel port
        try:
            self.pp = ParallelPort(self.dataAddress)
        except RuntimeError as e:
            self.log("Warning: %s"%str(e))
            self.pp = None
            pass
            
    def start(self, dt=0, duration=-1, configName=None):
        BasicModule.start(self, dt, duration, configName)     
        #Prepare the parallel port for reading mode
        self.write(32)
        
    def stop(self, dt=0):
        BasicModule.stop(self, dt)

    def cleanup(self):
        BasicModule.cleanup(self)
        
    def write(self, tcode):
        if self.pp is not None:
                self.pp.write(tcode, self.controlAddress)

    def getData(self):
        self.read()
        return self.data
     
    def getStatus(self):
        self.read()
        return self.status
   
    def getControl(self):
        self.read()
        return self.control
                
    def read(self):
        if self.pp is not None:
            dataCode = self.pp.read(self.dataAddress)
            statusCode = self.pp.read(self.statusAddress)
            controlCode = self.pp.read(self.controlAddress)
            print dataCode,
            print "-",
            print statusCode,
            print "-",
            print controlCode
            self.data = dataCode
            self.status = statusCode
            self.control = controlCode
            if self.csvLogger :
                self.csvLogger.writerow([self.controller.gTimeManager.experimentTime(), self.controller._currentRoutine, self.controller._currentCondition, dataCode, statusCode, controlCode])