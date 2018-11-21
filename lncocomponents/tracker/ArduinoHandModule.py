'''
Created on Jan 29, 2011

@author: bh
@since: winter 2010

@license: Distributed under the terms of the GNU General Public License (GPL).
'''

from os import path
import csv, re
import threading
import serial

from datetime import datetime
from pyglet.gl import *
import numpy as np
from time import sleep

#pylnco modules
from display.tools import *
from abstract.AbstractClasses import DrawableHUDSourceModule
from controller import getPathFromString
from tracker.bufferBox import BufferBox
from pyglet.clock import _default_time_function as time

# epsilon for float comparison
epsilon = 0.1
        
class Arduino(serial.Serial):
    def __init__(self, *args, **kwargs):
        #ensure that a reasonable timeout is set
        timeout = kwargs.get('timeout',0.1)
        if timeout < 0.01: timeout = 0.1
        kwargs['timeout'] = timeout
        serial.Serial.__init__(self, *args, **kwargs)
        self.buf = ''
        # init 
        self.flushInput()

    def readData(self, timeout=1):
    
        self.flushInput()
        self.buf = ''

        while len(self.buf) < 7 or self.buf[0] != '[' or self.buf.count(']') == 0:
            self.buf = self.readline()
        data = re.split('[\[,\]]', self.buf)
        #return [ float(f) for f in data[1:-1] ]#this gives an error from time to time. we therefore try this:
        #print "data gives:"
        #print data
        if (len(data)> 0):
            #return [ float(f) for f in data[1:-1] ]
            returnval=[]
            for f in data[1:-1]:
                if(bool(f)):#it is not empty
                    returnval.append(float(f))
                else:
                    returnval.append(1002)
                    
            #print "returnval: ", returnval
            return returnval
            
        else:
            return 1001.0

class ModuleMain(DrawableHUDSourceModule):
    """
    A simple module to read data from FreeSpace sensor.
    libfreespace can be found at http://libfreespace.hillcrestlabs.com/node
    """
    defaultInitConf = {
        'name': 'arduinohand',
        'port': 'COM1',
        'stabilization': 1,
        'logToCSV': True
    }
    
    defaultRunConf = {
        'asynchronous': False,
        'asynchrony_percent': 80
    }
    
    confDescription = [
        ('name', 'str', "Your bvp tracker"),
        ('port', 'str', "Computer port where sensor is plugged", ['COM1', 'COM2', 'COM3', 'COM4','COM5', 'COM6', 'COM7', 'COM8','COM9', 'COM10', 'COM11', 'COM12']),
        ('logToCSV', 'bool', "Save data to coma-separated-values file ( <modulename>_<date>.csv )"),
        #('stabilization', 'int', "Duration of the stabilization waiting (in seconds)"),
        ('asynchronous', 'bool', "Display in asynchronous way"),
    ]
    
    
    def __init__(self, controller, initConfig=None, runConfigs=None):
        DrawableHUDSourceModule.__init__(self, controller, initConfig, runConfigs)
                
        self.label = None
        self.value = 0.0
        #self.value_sync = 0.0
        #self.asynchronous = True
        #self.t_error = 0.0
        #self.index = 0                
         
        self.measure = [1001.0, 1001.0, 1001.0, 1001.0, 1001.0]
        # init 
        self.logActive = self.initConf['logToCSV']
        if self.logActive:
            now = datetime.today()
            self.csvLogger = csv.writer(open(path.join(self.controller.gLogger.Path, now.strftime('%y%m%d%H%M%S_') + self.initConf['name'] +  '.csv') , 'w'), lineterminator = '\n')
            line = [ 'expe_time', 'Routine', 'Condition', 'finger1', 'finger2', 'finger3', 'finger4', 'finger5' ]
            self.csvLogger.writerow(line)
            #print('just set the CSV...')
                
        # buffered variables

        self.values = BufferBox(10.0)
        self.finger1 = BufferBox(10.0)
        self.finger2 = BufferBox(10.0)
        self.finger3 = BufferBox(10.0)
        self.finger4 = BufferBox(10.0)
        self.finger5 = BufferBox(10.0)
        
        
        # init sensor
        print('trying to connect to arduinohand hardware............')
        self.sensor = Arduino(port=self.initConf['port'], baudrate=115200)
        #self.sensor = Arduino(port=self.initConf['port'], baudrate=9600)
        print('connected!')
         
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
            
            self.label2 = pyglet.text.Label(text='',
                                       color=( 0,255, 0, 255),
                                       font_name='arial',
                                       font_size=20,
                                       anchor_x='left', anchor_y='center',
                                       width=600, multiline=False,
                                       x=100, y=50)
            
        
        self.label.draw()   
        self.label2.draw()
        
        now = time()
       
        
            
    def start(self, dt=0, duration=-1, configName=None):
        """
        Activate the optic flow engine with the parameters passed in the conf
        """
        DrawableHUDSourceModule.start(self, dt, duration, configName)
            
        #self.asynchronous = self.activeConf['asynchronous']
        #self.async_percent = self.activeConf['asynchrony_percent'] / 100.0
        
        #now = time()
        #self.bpmtime_sync = now
        #self.bpmtime_async = now

        #measure = self.sensor.readData()
        #self.sensorValues.appendValue( now, measure[0])
        #self.value_sync = measure[1]

        pyglet.clock.schedule(self.update)  
        
    def stop(self, dt=0):
        DrawableHUDSourceModule.stop(self, dt)
        pyglet.clock.unschedule(self.update)
        
    def cleanup(self):
        DrawableHUDSourceModule.cleanup(self)
        
        # ensure serial port is closed
        self.sensor.close()
        del self.sensor
        self.sensor = None
        
        
    def update(self, dt):
        """
        The update is called regularly to update  data
        """
        # global EMA_alpha, epsilon
        # self.value_sync = 0.0
        # value_async = 0.0
        # beat_sync = 0.0
        # beat_async = 0.0
        # period = 0
        now = time()
        
        # get the data with lock mechanism
        self.measure = self.sensor.readData()
        while len(self.measure) < 5 :
            print('for some reason the length of the measure is') 
            print(len(self.measure))
            print('we add 1001 values...\n')
            self.measure.append(1001.0)
            
        self.finger1.appendValue( now, self.measure[0])
        self.finger2.appendValue( now, self.measure[1])
        self.finger3.appendValue( now, self.measure[2])
        self.finger4.appendValue( now, self.measure[3])
        self.finger5.appendValue( now, self.measure[4])
        
        #self.value_sync = measure[1]
        
        
        # if self.asynchronous:
            # # apply multiplying factor to speed up or slow down playing of the template
            # dt *= (self.async_percent * 65.0) / self.template_bpm
            # # start detection of next time with previous error in dt
            # t = self.t_error
            # # while the t is before the dt we want
            # while t < dt:
                # # find the index in template timings
                # self.index = (self.index + 1)%(len(self.template)-1)
                # t += self.template[self.index][0]
            # # we passed the dt by t-dt
            # self.t_error = t - dt
            # # interpolate linearly between the values
            # if self.template[self.index][0] == 0:
                # percent = self.t_error
            # else:
                # percent = self.t_error / self.template[self.index][0]
            # value_async = (1.0 - percent) * self.template[self.index][1] + percent * self.template[self.index - 1][1]
            
            # self.values.appendValue( now, value_async)
            # self.beat = beat_async 
            
            # self.value = value_async
            
            
        # else:
            # # sync = just the value
            # self.values.appendValue( now, self.value_sync)
            # self.beat = beat_sync
            
            # self.value = self.value_sync
            

        # fill in logs if required
        if self.logActive:
            # log time
            line = [ str("%.4f"%self.controller.gTimeManager.experimentTime()), self.controller._currentRoutine, self.controller._currentCondition ]
            # log coordinates
#            line.extend([self.value_sync, beat_sync, self.value, beat_async ])
            # line.extend([self.sensorValues.getValue(), self.value_sync, beat_sync * self.bpm_sync.getAverage(), value_async, beat_async * self.bpm_async.getAverage() ])
            line.extend([self.finger1.getValue(),self.finger2.getValue(),self.finger3.getValue(),self.finger4.getValue(),self.finger5.getValue() ])
            self.csvLogger.writerow(line)

    def getData(self):
        """
        For abstract interface (reactor is a source module). Keeping getPositions() for old calls to positions
        """
        DrawableHUDSourceModule.getData(self)
        return self.value

    def getUpdateInterval(self):
        """
        For abstract interface (reactor is a source module). 
        """
        return DrawableHUDSourceModule.getUpdateInterval(self)
