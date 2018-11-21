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
        return [ float(f) for f in data[1:-1] ]


class ModuleMain(DrawableHUDSourceModule):
    """
    A simple module to read data from FreeSpace sensor.
    libfreespace can be found at http://libfreespace.hillcrestlabs.com/node
    """
    defaultInitConf = {
        'name': 'Resp',
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
        ('stabilization', 'int', "Duration of the stabilization waiting (in seconds)"),
        ('asynchronous', 'bool', "Display in asynchronous way"),
        ('asynchrony_percent', 'int', "Percent of heart beat frequency to display asynchronously (e.g. 80, or 120)"),
        ('getData()', 'info', "Value synchronous or asynchronous with measure [0 1.0]."),
        ('beat', 'info', "Synchronous or asynchronous beat (binary state 0 or 1)."),
    ]
    
    
    def __init__(self, controller, initConfig=None, runConfigs=None):
        DrawableHUDSourceModule.__init__(self, controller, initConfig, runConfigs)
                
        self.label = None
        self.value = 0.0
        self.value_sync = 0.0
        self.beat = 0
        self.bpmtime_sync = 0.0
        self.bpmtime_async = 0.0
        self.template = []
        self.asynchronous = True
        self.t_error = 0.0
        self.index = 0                
                
        # init 
        self.logActive = self.initConf['logToCSV']
        if self.logActive:
            now = datetime.today()
            self.csvLogger = csv.writer(open(path.join(self.controller.gLogger.Path, now.strftime('%y%m%d%H%M%S_') + self.initConf['name'] +  '.csv') , 'w'), lineterminator = '\n')
            line = [ 'expe_time', 'Routine', 'Condition', 'sensor', 'sync', 'sync_beat', 'async', 'async_beat' ]
            self.csvLogger.writerow(line)
        
        # load templace data
        filename = path.join( path.dirname(__file__),  "bvp_template_estelle_65bpm.csv" )
        templatereader = csv.reader(open(filename))
        for l in templatereader:
            self.template.append( [ float(l[0]), float(l[1]) ] )
        # template data average frequency (BPM)
        self.template_bpm = 65.0
        
        # buffered variables
        self.bpm_sync = BufferBox(30.0)
        self.bpm_async = BufferBox(30.0)
        self.values = BufferBox(10.0)
        self.sensorValues = BufferBox(10.0)
            
        # init sensor
        self.sensor = Arduino(port=self.initConf['port'], baudrate=115200)
        
        self.log( 'Waiting %d seconds for Respiration sensor to stabilize...'%self.initConf['stabilization'])
        sleep(self.initConf['stabilization'])
            
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
            
        if self.asynchronous:     
            self.label.text = 'subject %.1f - %.1f bpm'%((self.value_sync), self.bpm_sync.getAverage())
            self.label2.text  = 'display %.1f - %.1f bpm'%((self.value), self.bpm_async.getAverage())
        else:
            self.label.text  = 'subject %.1f - %.1f bpm'%((self.value), self.bpm_sync.getAverage())
            self.label2.text = 'display identical'
        self.label.draw()   
        self.label2.draw()
        
        now = time()
        # plot sensorValue 
        glColor4f(1,1,0,1)
        glBegin(GL_LINE_LOOP)
        glVertex2f( - 50, -1)
        glVertex2f( - 50,  window_height / 2)
        for mst in self.sensorValues.orderedkeys[0:-1:2]:
            t = now - float(mst) / 1000000.0
            y = self.sensorValues.valuestack[mst] / 10.0
            glVertex2f( window_width * (10.0-t) / 10.0 , y * window_height / 2 + window_height / 2)
        glVertex2f(window_width +50, -1)
        glEnd()
        # plot value (respiration)
        glColor4f(1,0,0,1)
        glLineWidth(3)
        glBegin(GL_LINE_LOOP)
        glVertex2f( -50, -1)
        glVertex2f( - 50,  window_height / 2)
        for mst in self.values.orderedkeys[0:-1:2]:
            t = now - float(mst) / 1000000.0
            y = self.values.valuestack[mst] / 10.0
            glVertex2f( window_width * (10.0-t) / 10.0 , y * window_height / 2 + window_height / 2)
        glVertex2f(window_width +50, -1)
        glEnd()
        
            
    def start(self, dt=0, duration=-1, configName=None):
        """
        Activate the optic flow engine with the parameters passed in the conf
        """
        DrawableHUDSourceModule.start(self, dt, duration, configName)
            
        self.asynchronous = self.activeConf['asynchronous']
        self.async_percent = self.activeConf['asynchrony_percent'] / 100.0
        
        now = time()
        self.bpmtime_sync = now
        self.bpmtime_async = now

        measure = self.sensor.readData()
        self.sensorValues.appendValue( now, measure[0])
        self.value_sync = measure[1]

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
        The update is called regularly to update angle data
        """
        if not self.started:
            return
            
        global epsilon
        self.value_sync = 0.0
        value_async = 0.0
        beat_sync = 0.0
        beat_async = 0.0
        period = 0
        now = time()
        
        # get the data with lock mechanism
        measure = self.sensor.readData()
        self.sensorValues.appendValue( now, measure[0])
        self.value_sync = measure[1]
        
        # # detect peak
        # if (self.sensorValues.getValue() - self.sensorValues.getAverage()) < -8.0 and self.sensorValues.getValue(now - 0.05) > 1.0 and self.sensorValues.getValue() < 1.0:
            # tmptime = now
            # period = tmptime - self.bpmtime_sync
            # self.bpmtime_sync = tmptime
            # # peak detected in a reasonable time period (avoid duplicates)
            # if period > 1.0 and period < 10.0:
                # beat_sync = 1.0
                # self.bpm_sync.appendValue(now, ( 1.0 / period ) * 60.0 )
                # #print 'peak', self.bpm_sync.getValue()
        
        if self.asynchronous:
            # apply multiplying factor to speed up or slow down playing of the template
            dt *= (self.async_percent * 65.0) / self.template_bpm
            # start detection of next time with previous error in dt
            t = self.t_error
            # while the t is before the dt we want
            while t < dt:
                # find the index in template timings
                self.index = (self.index + 1)%(len(self.template)-1)
                t += self.template[self.index][0]
            # we passed the dt by t-dt
            self.t_error = t - dt
            # interpolate linearly between the values
            if self.template[self.index][0] == 0:
                percent = self.t_error
            else:
                percent = self.t_error / self.template[self.index][0]
            value_async = (1.0 - percent) * self.template[self.index][1] + percent * self.template[self.index - 1][1]
            
            # # detect peak
            # self.measures_async[2] = self.measures_async[1]
            # self.measures_async[1] = self.measures_async[0]
            # self.measures_async[0] = value_async
            # if self.measures_async[0] > 0.3 and self.measures_async[2] < (self.measures_async[1] - epsilon) and ( self.measures_async[0] < self.measures_async[1] or abs(self.measures_async[0]-self.measures_async[1])<epsilon ) :
                # tmptime = now
                # period = tmptime - self.bpmtime_async
                # self.bpmtime_async = tmptime
                # if period > 0.3:
                    # beat_async = 1.0
                    # self.bpm_async.appendValue(now, ( 1.0 / period ) * 60.0 )

            self.values.appendValue( now, value_async)
            self.beat = beat_async 
            
            
            self.value = value_async
            
            
        else:
            # sync = just the value
            self.values.appendValue( now, self.value_sync)
            self.beat = beat_sync
            
            self.value = self.value_sync
            
        # set the final value (after first beat and according to latency)
        # if self.bpm_sync.getLength() > 1 :
            # if self.latency > 0.0:
                # period = 60.0 / self.bpm_async.getAverage() if self.asynchronous else 60.0 / self.bpm_sync.getAverage()
                # self.value = self.values.getValue( now - period + self.latency )
            # else:
                # self.value = self.values.getValue()
        # else:
            # self.value = 0.0
            
        # fill in logs if required
        if self.logActive:
            # log time
            line = [ str("%.4f"%self.controller.gTimeManager.experimentTime()), self.controller._currentRoutine, self.controller._currentCondition ]
            # log coordinates
#            line.extend([self.value_sync, beat_sync, self.value, beat_async ])
            # line.extend([self.sensorValues.getValue(), self.value_sync, beat_sync * self.bpm_sync.getAverage(), value_async, beat_async * self.bpm_async.getAverage() ])
            line.extend([self.sensorValues.getValue(), self.value_sync, 0, value_async, 0 ])
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
