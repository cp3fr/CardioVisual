'''
Created on Jan 29, 2011

@author: bh
@since: winter 2010

@license: Distributed under the terms of the GNU General Public License (GPL).
'''

from os import path
import csv
import threading, time
import serial

from datetime import datetime
from pyglet.gl import *
import numpy as np

#pylnco modules
from display.tools import *
from abstract.AbstractClasses import DrawableHUDSourceModule
from controller import getPathFromString

# exponential moving average alpha coeficient for 10 values decay
EMA_alpha = 2.0 / (10.0 + 1.0)
# epsilon for float comparison
epsilon = 0.01
        
class Arduino(serial.Serial):
    def __init__(self, *args, **kwargs):
        #ensure that a reasonable timeout is set
        timeout = kwargs.get('timeout',0.1)
        if timeout < 0.01: timeout = 0.1
        kwargs['timeout'] = timeout
        serial.Serial.__init__(self, *args, **kwargs)
        self.buf = '0.0'
        # init 
        self.flushInput()

    def readData(self, timeout=1):
        try:
            # read sensor data and extract values
            self.buf = self.readline()
            #self.flushInput()
        except:
            pass
        
        if len(self.buf) < 3:
            return []
        return self.buf.split(',')


class arduinoUpdateThread ( threading.Thread ):
    def __init__(self, parent = None):
        threading.Thread.__init__(self)
        self.module = parent
        
    def run(self):
        while True:
            # get the lock for the thread
            self.module.lock.acquire()
            # read data
            if self.module.sensor is not None:
                self.module.measure = self.module.sensor.readData()
            else:
            # exit if sensor set to None
                break
            # free the lock for the module
            self.module.lock.release()
            # necessary to give the main thread time to acquire lock
            time.sleep(0.005)

            
class ModuleMain(DrawableHUDSourceModule):
    """
    A simple module to read data from FreeSpace sensor.
    libfreespace can be found at http://libfreespace.hillcrestlabs.com/node
    """
    defaultInitConf = {
        'name': 'arduino',
        'port': 'COM3',
        'logToCSV': True
    }
    
    defaultRunConf = {
    }
    
    confDescription = [
        ('name', 'str', "Your bvp tracker"),
        ('port', 'str', "Computer port where sensor is plugged", ['COM1', 'COM2', 'COM3', 'COM4','COM5', 'COM6', 'COM7', 'COM8','COM9', 'COM10', 'COM11', 'COM12']),
        ('logToCSV', 'bool', "Save data to coma-separated-values file ( <date>_<modulename>.csv )"),
        ('values', 'info', "Values (array) read from Arduino."),
    ]
    

    
    def __init__(self, controller, initConfig=None, runConfigs=None):
        DrawableHUDSourceModule.__init__(self, controller, initConfig, runConfigs)
                
        self.label = None
        self.values = []
        self.measure = []
        self.measures = []
                
        # init 
        self.logActive = self.initConf['logToCSV']
        if self.logActive:
            now = datetime.today()
            self.csvLogger = csv.writer(open(path.join(self.controller.gLogger.Path, now.strftime('%y%m%d%H%M%S_') + self.initConf['name'] +  '.csv') , 'w'), lineterminator = '\n')
            line = [ 'expe_time', 'Routine', 'Condition' ]
            self.csvLogger.writerow(line)
        
        # init sensor
        self.sensor = Arduino(port=self.initConf['port'], baudrate=9600)
        self.measure = self.sensor.readData()
        self.measures.append(self.measure)

        # create and start thread
        self.lock = threading.Lock()
        self.thread = arduinoUpdateThread(parent=self)
        self.thread.start()
            
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
            
        self.label.text = 'Arduino data %s'%self.values
        self.label.draw() 

    def start(self, dt=0, duration=-1, configName=None):
        DrawableHUDSourceModule.start(self, dt, duration, configName)
        pyglet.clock.schedule(self.update)  

    def stop(self, dt=0):
        DrawableHUDSourceModule.stop(self, dt)
        pyglet.clock.unschedule(self.update)
        
    def cleanup(self):
        DrawableHUDSourceModule.cleanup(self)
        
        # request stop and wait for the thread to terminate
        self.lock.acquire()
        self.sensor.close()
        del self.sensor
        self.sensor = None
        self.lock.release()
        self.thread.join(1.0)
        
        
    def update(self, dt):
        """
        The update is called regularly to update data
        """
        x = 0.0
        
        # get the data with lock mechanism
        if self.lock.acquire():
            x = self.measure
            # free the lock
            self.lock.release()

        self.values = x
        
        # fill in logs if required
        if self.logActive:
            # log time
            line = [ str("%.4f"%self.controller.gTimeManager.experimentTime()), self.controller._currentRoutine, self.controller._currentCondition ]
            # log coordinates
            line.extend( self.values )
            self.csvLogger.writerow(line)


    def getData(self):
        """
        For abstract interface (reactor is a source module). Keeping getPositions() for old calls to positions
        """
        DrawableHUDSourceModule.getData(self)
        return self.values

    def getUpdateInterval(self):
        """
        For abstract interface (reactor is a source module). 
        """
        return DrawableHUDSourceModule.getUpdateInterval(self)
