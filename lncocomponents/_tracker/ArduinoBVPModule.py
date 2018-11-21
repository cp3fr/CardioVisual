'''
Created on Jan 29, 2011

@author: bh
@since: winter 2010

@license: Distributed under the terms of the GNU General Public License (GPL).
'''

from os import path
import csv
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
            self.buf = '0.0'
        return float(self.buf) / 1024.0


class arduinoUpdateThread ( threading.Thread ):
        
    def __init__(self, parent = None):
        threading.Thread.__init__(self)
        self.module = parent
        self.measure = 0.0
        
    def run(self):
        while True:
            # get the lock for the thread
            self.module.lock.acquire()
            # read data
            if self.module.sensor is not None:
                self.measure = self.module.sensor.readData()
            else:
            # exit if sensor set to None
                break
            # free the lock for the module
            self.module.lock.release()
            # necessary to give the main thread time to acquire lock
            sleep(0.005)

            
class ModuleMain(DrawableHUDSourceModule):
    """
    A simple module to read data from FreeSpace sensor.
    libfreespace can be found at http://libfreespace.hillcrestlabs.com/node
    """
    defaultInitConf = {
        'name': 'BVP',
        'port': 'COM3',
        'logToCSV': True
    }
    
    defaultRunConf = {
        'asynchronous': False,
        'asynchrony_percent': 80,
        'ECG_BVP_latency': 0.0
    }
    
    confDescription = [
        ('name', 'str', "Your bvp tracker"),
        ('port', 'str', "Computer port where sensor is plugged", ['COM1', 'COM2', 'COM3', 'COM4','COM5', 'COM6', 'COM7', 'COM8','COM9', 'COM10', 'COM11', 'COM12']),
        ('logToCSV', 'bool', "Save data to coma-separated-values file ( <modulename>_<date>.csv )"),
        ('asynchronous', 'bool', "Display in asynchronous way"),
        ('asynchrony_percent', 'int', "Percent of heart beat frequency to display asynchronously (e.g. 80, or 120)"),
        ('ECG_BVP_latency', 'float', "Measure of latency (in seconds) between ECG and blood pressure peak (used to sync flash with ECG instead of BVP)"),
        ('value', 'info', "Value synchronous or asynchronous with measure [0 1.0]."),
        ('beat', 'info', "Synchronous or asynchronous beat (binary state 0 or 1)."),
    ]
    
    
    def __init__(self, controller, initConfig=None, runConfigs=None):
        DrawableHUDSourceModule.__init__(self, controller, initConfig, runConfigs)
                
        self.label = None
        self.value = 0.0
        self.beat = 0
        self.measures_sync = [0.0, 0.0, 0.0]
        self.bpmtime_sync = 0.0
        self.measures_async = [0.0, 0.0, 0.0]
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
            line = [ 'expe_time', 'Routine', 'Condition', 'sync', 'sync_beat', 'async', 'async_beat', 'afterLatency' ]
            self.csvLogger.writerow(line)
        
        # load templace data
        filename = path.join( path.dirname(__file__),  "bvp_template_estelle_65bpm.csv" )
        templatereader = csv.reader(open(filename))
        for l in templatereader:
            self.template.append( [ float(l[0]), float(l[1]) ] )
        # template data average frequency (BPM)
        self.template_bpm = 65.0
        
        # buffered variables
        self.bpm_sync = BufferBox(10.0)
        self.bpm_async = BufferBox(10.0)
        self.values = BufferBox(3.0)
            
        # init sensor
        self.sensor = Arduino(port=self.initConf['port'], baudrate=9600)

        # create and start thread
        self.lock = threading.Lock()
        self.thread = arduinoUpdateThread(parent=self)
        self.thread.measure = self.sensor.readData()
        self.measures_sync[0] = self.thread.measure
        self.measures_sync[1] = self.thread.measure
        self.measures_sync[2] = self.thread.measure
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
            
            self.label2 = pyglet.text.Label(text='',
                                       color=( 0,255, 0, 255),
                                       font_name='arial',
                                       font_size=20,
                                       anchor_x='left', anchor_y='center',
                                       width=600, multiline=False,
                                       x=100, y=50)
            
        if self.asynchronous:     
            self.label.text = 'subject %.1f %% %.1f bpm'%((self.measures_sync[0]*100.0), self.bpm_sync.getAverage())
            self.label2.text  = 'display %.1f %% %.1f bpm'%((self.value*100.0), self.bpm_async.getAverage())
        else:
            self.label.text  = 'subject %.1f %% %.1f bpm'%((self.value*100.0), self.bpm_sync.getAverage())
            self.label2.text = 'display identical'
        self.label.draw()   
        self.label2.draw()
            
    def start(self, dt=0, duration=-1, configName=None):
        """
        Activate the optic flow engine with the parameters passed in the conf
        """
        DrawableHUDSourceModule.start(self, dt, duration, configName)
            
        self.asynchronous = self.activeConf['asynchronous']
        self.async_percent = self.activeConf['asynchrony_percent'] / 100.0
        self.latency = self.activeConf['ECG_BVP_latency']
        
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
        The update is called regularly to update angle data
        """
        global EMA_alpha, epsilon
        value_sync = 0.0
        value_async = 0.0
        beat_sync = 0.0
        beat_async = 0.0
        period = 0
        now = time()
        
        # get the data with lock mechanism
        if self.lock.acquire():
            value_sync = self.thread.measure
            # free the lock
            self.lock.release()
        
        # detect peak
        self.measures_sync[2] = self.measures_sync[1]
        self.measures_sync[1] = self.measures_sync[0]
        self.measures_sync[0] = value_sync
        if self.measures_sync[0] > 0.3 and self.measures_sync[2] < (self.measures_sync[1] - epsilon) and ( self.measures_sync[0] < self.measures_sync[1] or abs(self.measures_sync[0]-self.measures_sync[1])<epsilon ) :
            tmptime = now
            period = tmptime - self.bpmtime_sync
            self.bpmtime_sync = tmptime
            # peak detected in a reasonable time period
            if period > 0.3 and period < 2.0:
                beat_sync = 1.0
                self.bpm_sync.appendValue(now, ( 1.0 / period ) * 60.0 )
        
        if self.asynchronous:
            # apply multiplying factor to speed up or slow down playing of the template
            dt *= (self.async_percent * self.bpm_sync.getAverage()) / self.template_bpm
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
            
            # detect peak
            self.measures_async[2] = self.measures_async[1]
            self.measures_async[1] = self.measures_async[0]
            self.measures_async[0] = value_async
            if self.measures_async[0] > 0.3 and self.measures_async[2] < (self.measures_async[1] - epsilon) and ( self.measures_async[0] < self.measures_async[1] or abs(self.measures_async[0]-self.measures_async[1])<epsilon ) :
                tmptime = now
                period = tmptime - self.bpmtime_async
                self.bpmtime_async = tmptime
                if period > 0.3:
                    beat_async = 1.0
                    self.bpm_async.appendValue(now, ( 1.0 / period ) * 60.0 )

            self.values.appendValue( now, value_async)
            self.beat = beat_async 
        else:
            # sync = just the value
            self.values.appendValue( now, value_sync)
            self.beat = beat_sync
            
        # set the final value (after first beat and according to latency)
        if self.bpm_sync.getLength() > 1 :
            if self.latency > 0.0:
                period = 60.0 / self.bpm_async.getAverage() if self.asynchronous else 60.0 / self.bpm_sync.getAverage()
                self.value = self.values.getValue( now - period + self.latency )
            else:
                self.value = self.values.getValue()
        else:
            self.value = 0.0
            
        # fill in logs if required
        if self.logActive:
            # log time
            line = [ str("%.4f"%self.controller.gTimeManager.experimentTime()), self.controller._currentRoutine, self.controller._currentCondition ]
            # log coordinates
#            line.extend([value_sync, beat_sync, self.value, beat_async ])
            line.extend([value_sync, beat_sync * self.bpm_sync.getAverage(), value_async, beat_async * self.bpm_async.getAverage(), self.value ])
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
