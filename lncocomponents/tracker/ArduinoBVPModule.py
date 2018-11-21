'''
Created on Jan 29, 2011

@author: bh
@since: winter 2010
@modified: Spring 2013(Javier Bello Ruiz)

@license: Distributed under the terms of the GNU General Public License (GPL).
'''

from os import path
import csv, re
import threading
import serial

import numpy as np
from time import sleep
from datetime import datetime
from pyglet.gl import *
from pyglet.clock import _default_time_function as time

# LNCO modules
from display.tools import *
from tracker.bufferBox import BufferBox
from controller import getPathFromString
from abstract.AbstractClasses import DrawableHUDSourceModule
        
class Arduino(serial.Serial):
            
    def readData(self, timeout=1):
        try:
            # Read sensor data and extract values
            self.buf = self.readline()
        except:
            self.buf = ''
        if len(self.buf) < 3:
            return 0.0
        try :
            data = float(self.buf) / 1024.0
        except:
            data = 0.0
        self.buf = ''
        return data

class arduinoUpdateThread ( threading.Thread ):

    def __init__(self, parent = None):
        threading.Thread.__init__(self)
        self.module = parent

    def run(self):
    
        while True:
            # Get the lock for the thread
            self.module.lock.acquire()
            # Read data
            if self.module.sensor is not None:
                measure = self.module.sensor.readData()
                
                now = time()
                # Detect contiguous  peaks for bpm
                value = measure
                beat = False
                period = 0.0
                if (self.module.bpmtime[100] < 0.0) : self.module.bpmtime[100] = now
                
                # Filter the raw value if required ???????????????????????????????????????
                """
                if self.module.filter_value is not None:
                    self.module.filter_value.appendValue(now, value)
                    value = self.module.filter_value.getAverage()
                """
                self.module.measures[100][2] = self.module.measures[100][1]
                self.module.measures[100][1] = self.module.measures[100][0]
                self.module.measures[100][0] = value
                beat = self.module.measures[100][0] > 0.3 and self.module.measures[100][2] < (self.module.measures[100][1] - self.module.epsilon) and (self.module.measures[100][0] < self.module.measures[100][1] or abs(self.module.measures[100][0]-self.module.measures[100][1]) < self.module.epsilon)
                
                if beat:
                    period = now - self.module.bpmtime[100]
                    self.module.bpmtime[100] = now
                    # Peak detected in a reasonable time period
                    if (period > 0.4) and (period < 1.2):
                        beat = True
                        self.module.bpm[100].appendValue(now, 60.0/period)
                    else: beat = False
                
                key = long(now*1000000.0)
                self.module.values[100][key] = value
                self.module.beats[100][key] = beat
                self.module.orderedKeys.append(key)
                
                if (self.module.previousTime < 0.0) : self.module.previousTime = now
                dt = now - self.module.previousTime
                self.module.previousTime = now
                
                if self.module.logActive:
                    # Log BVP signal
                    row = [str("%.6f"%dt), str("%.6f"%value), str("%d"%beat)]
                    self.module.csvBVP.writerow(row)
                    
                for percentage in self.module.percentages:
                    
                    self.module.mulFactor[percentage] = (float(percentage)/100.0 * self.module.bpm[100].getAverage()) / self.module.template_bpm
                     # Asynchronous: apply multiplying factor to speed up or slow down playing of the template
                    auxdt = dt * self.module.mulFactor[percentage]
                    # Start detection of next time with previous error in dt
                    t = self.module.t_error[percentage]
                    
                    value_async = 0.0
                    beat_async = False
                    
                    # While the t is before the dt we want
                    while t < auxdt:
                        # To find the index in template timings
                        self.module.index[percentage] = (self.module.index[percentage] + 1)%len(self.module.template)
                        t += self.module.template[self.module.index[percentage]][0]
                        #beat_async = bool(self.module.template[self.module.index[percentage]][2]) or beat_async
                    
                    # We passed the dt by t-dt
                    self.module.t_error[percentage] = t - auxdt
                    
                    # Interpolate linearly between the values
                    if self.module.template[self.module.index[percentage]][0] == 0:
                        percent = self.module.t_error[percentage] 
                    else:
                        percent = self.module.t_error[percentage]  / self.module.template[self.module.index[percentage]][0]

                    value_async = percent * self.module.template[self.module.index[percentage]][1] + (1.0 - percent) * self.module.template[self.module.index[percentage] - 1][1]

                    period = 0.0
                    if (self.module.bpmtime[percentage] < 0.0) : self.module.bpmtime[percentage] = now
                    
                    if self.module.filter_value is not None:
                        self.module.filter_value.appendValue(now, value_async)
                        value_async = self.module.filter_value.getAverage()
                    #Could I detect the peak in the template?
                    self.module.measures[percentage][2] = self.module.measures[percentage][1]
                    self.module.measures[percentage][1] = self.module.measures[percentage][0]
                    self.module.measures[percentage][0] = value_async
                    beat_async = self.module.measures[percentage][0] > 0.3 and self.module.measures[percentage][2] < (self.module.measures[percentage][1] - self.module.epsilon) and (self.module.measures[percentage][0] < self.module.measures[percentage][1] or abs(self.module.measures[percentage][0]-self.module.measures[percentage][1]) < self.module.epsilon)
                    beat_async = self.module.measures[percentage][0] > 0.3 and self.module.measures[percentage][2] < (self.module.measures[percentage][1] - self.module.epsilon) and (self.module.measures[percentage][0] < self.module.measures[percentage][1] or abs(self.module.measures[percentage][0]-self.module.measures[percentage][1]) < self.module.epsilon)
                    
                    if beat_async:
                        period = now - self.module.bpmtime[percentage]
                        self.module.bpmtime[percentage] = now
                        # Peak detected in a reasonable time period
                        if (period > 0.3) and (period < 2.0):
                            beat_async = True
                            self.module.bpm[percentage].appendValue(now, 60.0/period)
                        else: beat_async = False
                    
                    self.module.values[percentage][key] = value_async
                    self.module.beats[percentage][key] = beat_async
                    
                    if self.module.logActive:
                        # Log BVP async signal
                        row = [str("%.6f"%dt), str("%.6f"%value_async), str("%d"%beat_async)]
                        self.module.csvAsyncBVP[percentage].writerow(row)
                
                # Make sure time order is kept
                if (len(self.module.orderedKeys) > 2) and (self.module.orderedKeys[-1] < self.module.orderedKeys[-2]):
                    self.module.orderedKeys = sorted(self.module.orderedKeys)
                # Remove every value with an earlier key than max_duration ago 
                while self.module.orderedKeys[0] < (key - long((self.module.maxTime + 1)*1000000.0)):
                    if self.module.values[100].has_key(self.module.orderedKeys[0]):
                        self.module.values[100].pop(self.module.orderedKeys[0])
                        self.module.beats[100].pop(self.module.orderedKeys[0])
                        for percentage in self.module.percentages:
                            self.module.values[percentage].pop(self.module.orderedKeys[0])
                            self.module.beats[percentage].pop(self.module.orderedKeys[0])
                        self.module.orderedKeys.pop(0)
            else:
            # Exit if sensor set to None
                self.module.lock.release()
                break
            # Free the lock for the module
            self.module.lock.release()
            # Necessary to give the main thread time to acquire lock
            sleep(0)
            
class ModuleMain(DrawableHUDSourceModule):

    defaultInitConf = {
        'name': 'BVP',
        'port': 'COM3',
        'logToCSV': True,
        'filter': 0,
        'N': 10
    }
    
    defaultRunConf = {
        'asynchronous': False,
        'asynchrony_percent': 80,
        'displayDebug': False,
        'ECG_BVP_latency': 0.0,
        'alphaGlowDuration': 500
    }
    
    confDescription = [
        ('name', 'str', "Your BVP tracker."),
        ('port', 'str', "Computer port where sensor is plugged in.", ['COM1', 'COM2', 'COM3', 'COM4','COM5', 'COM6', 'COM7', 'COM8','COM9', 'COM10', 'COM11', 'COM12']),
        ('logToCSV', 'bool', "Save data to coma-separated-values file (<date>_<modulename>.csv)."),
        ('filter', 'int', "If not 0, apply an exponential moving average filtering on the N latest mili-seconds."),
        ('N', 'int', "If filter not 0, N is the number of time periods to apply an an exponential moving average filtering."),
        ('asynchronous', 'bool', "Display in asynchronous way."),
        ('asynchrony_percent', 'int', "Percent of heart beat frequency to display asynchronously (e.g. 80, or 120)."),
        ('ECG_BVP_latency', 'float', "Measure of latency (in seconds) between ECG and blood pressure peak (used to sync flash with ECG instead of BVP)."),
        ('displayDebug', 'bool', "Display the debug signal (opposite condition to current)."),
        ('alphaGlowDuration', 'int', "Duration of the alpha glow animation in ms."),
        ('value', 'info', "Value synchronous or asynchronous with measure [0.0, 1.0]."),
        ('getAlphaGlow()', 'info', "Value to display the alpha glow [0.0, 1.0]"),
        ('beat', 'info', "Synchronous or asynchronous beat(binary value: 0 or 1).")
    ]
    
    
    def __init__(self, controller, initConfig=None, runConfigs=None):
        DrawableHUDSourceModule.__init__(self, controller, initConfig, runConfigs)
        
        self.template = []
        self.labelSubject = None
        self.asynchronous = False
        self.debug = False
        self.maxTime = 10.0
        self.lastKey = 0.0
        self.lastX = math.pi + 1.0
        self.alphaGlow = 0.0
        self.async_percent = 80.0
        
        self.value = 0.0
        self.value_sync = 0.0
        self.value_async = 0.0
        self.beat = False
        
        # Plot data
        self.plotAlpha = {}
        self.plotSync = {}
        self.plotAsync = {}
        self.plotBeats = {}
        self.plotOrderedKeys = []
        
        # Dictionaries
        self.measures = {}
        self.values = {}
        self.beats = {}
        self.bpm = {}
        self.bpmtime = {}
        self.mulFactor = {}
        self.t_error = {}
        self.index = {}
        
        self.percentages = []
        self.orderedKeys = []
        self.previousTime = -1.0
        
        #??????????????????????????????????????????????
        self.epsilon = 0.01
        
        # Sync
        self.measures[100] = [0.0, 0.0, 0.0]
        self.values[100] = {}
        self.beats[100] = {}
        self.bpm[100] = BufferBox(20.0)
        self.bpmtime[100] = -1.0
        self.mulFactor[100] = 0.0
        self.t_error[100] = 0.0
        self.index[100] = -1
        
        # Initialize logger 
        self.logActive = self.initConf['logToCSV']
        now = datetime.today()
        if self.logActive:
            self.csvLogger = csv.writer(open(path.join(self.controller.gLogger.Path, now.strftime('%y%m%d%H%M%S_') + self.initConf['name'] +  '.csv') , 'w'), lineterminator = '\n')
            self.csvBVP = csv.writer(open(path.join(self.controller.gLogger.Path, now.strftime('%y%m%d%H%M%S_') + 'BVPsignal' +  '.csv') , 'w'), lineterminator = '\n')
            line = ['exp_time', 'Routine', 'Condition', 'sync_value', 'sync_beat(bpm)', 'async_value', 'async_beat(bpm)', 'display_value', 'display_beat', 'alphaGlow_value']
            self.csvLogger.writerow(line)
        
        # Async
        self.csvAsyncBVP = {}
        for conf in self.runConfs.values():
            percentage = int(conf['asynchrony_percent'])
            if (percentage in self.percentages) or (percentage == 100):
                continue
            self.percentages.append(percentage)
            self.measures[percentage] = [0.0, 0.0, 0.0]
            self.values[percentage] = {}
            self.beats[percentage] = {}
            self.bpm[percentage] = BufferBox(20.0)
            self.bpmtime[percentage] = -1.0
            self.mulFactor[percentage] = 0.0
            self.t_error[percentage] = 0.0
            self.index[percentage] = -1
            self.csvAsyncBVP[percentage] = csv.writer(open(path.join(self.controller.gLogger.Path, now.strftime('%y%m%d%H%M%S_') + 'BVPasync' + str(percentage) + '.csv') , 'w'), lineterminator = '\n')
        
        # Load template data
        filename = path.join(path.dirname(__file__),  "bvp_template_estelle_65bpm.csv")
        templatereader = csv.reader(open(filename))
        for l in templatereader:
            self.template.append([float(l[0]), float(l[1])])
        # Template data average frequency (BPM)
        self.template_bpm = 65.0
        
        # Initialize sensor
        self.sensor = Arduino(port=self.initConf['port'], baudrate=115200)
        self.log('BVP sensor opened.')
        
        # Filter
        if self.initConf['filter'] > 0:
            if self.initConf['N'] > 0:
                self.filter_value = BufferBox(float(self.initConf['filter'])/1000.0, self.initConf['N'])
            else:
                self.filter_value = BufferBox(float(self.initConf['filter'])/1000.0)
        else:
            self.filter_value = None

        # Create and start the reading thread
        self.lock = threading.Lock()
        self.thread = arduinoUpdateThread(parent=self)
        self.thread.start()
        
        timeout = 0.0
        print "Starting BVP module",
        while ((len(self.bpm[100].valuestack) < 10) and (timeout < 5.0)):
            sleep(0.1)
            timeout += 0.1
            print ".",
            
    def draw(self, window_width, window_height):
        DrawableHUDSourceModule.draw(self, window_width, window_height)
        
        if self.labelSubject is None:
            self.labelSubject = pyglet.text.Label(text = '',
                                       color = (255, 0, 0, 255),
                                       font_name ='arial',
                                       font_size = 20,
                                       anchor_x = 'left', anchor_y = 'center',
                                       width = 600, multiline = False,
                                       x = 100, y = 100)
            
            self.labelCondition = pyglet.text.Label(text = '',
                                       color = ( 0,255, 0, 255),
                                       font_name = 'arial',
                                       font_size = 20,
                                       anchor_x = 'left', anchor_y = 'center',
                                       width = 600, multiline = False,
                                       x = 100, y = 50)
                                       
        self.labelSubject.text = 'Subject value: %.1f at %.1f bpm'%(self.value_sync, self.bpm[100].getAverage())
        if self.asynchronous:
            self.labelCondition.text  = 'Asynchronous display. Async value: %.1f at %.1f bpm'%(self.value_async, self.bpm[self.activePercent].getAverage())
        else:
            self.labelCondition.text = 'Synchronous display.'
        
        self.labelSubject.draw()   
        self.labelCondition.draw()
        
        # Plot sensor values
        now = float(self.plotOrderedKeys[-1])/1000000.0 if len(self.plotOrderedKeys) > 0 else time()
        
        if (not self.asynchronous) or self.debug:
            glColor4f(1, 1, 0, 1)
            glBegin(GL_LINE_LOOP)
            glVertex2f(-50, -1)
            glVertex2f(-50, window_height/2)
            for key in self.plotOrderedKeys:
                t = now - float(key)/1000000.0
                y = self.plotSync[key] / 3.0
                glVertex2f(window_width *(self.maxTime - t)/self.maxTime, y * window_height)
            glVertex2f(window_width + 50, -1)
            glEnd()
        
        if self.asynchronous or self.debug:
            glColor4f(1, 1, 1, 1)
            glBegin(GL_LINE_LOOP)
            glVertex2f(-50, -1)
            glVertex2f(-50, window_height/2)
            for key in self.plotOrderedKeys:
                t = now - float(key)/1000000.0
                y = self.plotAsync[key] / 3.0
                glVertex2f(window_width *(self.maxTime - t)/self.maxTime, y * window_height)
            glVertex2f(window_width + 50, -1)
            glEnd()
        
        glColor4f(1, 0, 0, 1)
        glBegin(GL_LINE_LOOP)
        glVertex2f(-50, -1)
        glVertex2f(-50, window_height/2)
        for key in self.plotOrderedKeys:
            t = now - float(key)/1000000.0
            y = self.plotAlpha[key]
            glVertex2f(window_width * (self.maxTime - t)/self.maxTime, y * window_height)
        glVertex2f(window_width + 50, -1)
        glEnd()
        
        glColor4f(1, 0, 0, 1)
        glPointSize(5)
        glBegin(GL_POINTS) 
        for key in self.plotOrderedKeys:
            t = now - float(key)/1000000.0
            y = 0.5
            if self.plotBeats[key]:
                glColor4f(1, 0, 0, 1)
                glVertex2f(window_width * (self.maxTime - t)/self.maxTime, y * window_height)
        glEnd()
        
    def update(self, dt):
        """
        The update is called regularly to update angle data
        """
        
        if (not self.started) or (len(self.orderedKeys) < 1):
            return
        
        keys = []
        if (self.lastKey != 0.0):
            previousKey = self.lastKey
            if self.lock.acquire():
                self.lastKey = self.orderedKeys[-1]
                if (self.orderedKeys.index(self.lastKey) != self.orderedKeys.index(previousKey)):
                    keys = self.orderedKeys[self.orderedKeys.index(previousKey):-1]
                self.lock.release()
        else:
            if self.lock.acquire():
                self.lastKey = self.orderedKeys[-1]
                self.lock.release()
                
        if (len(keys) < 1):
            return
        
        # value_sync = average of the data between previousKey and self.lastKey
        value_sync = 0.0
        beat_sync = False
        
        value_async = 0.0
        beat_async = False
        
        for key in keys:
            value_sync += self.values[100][key]
            beat_sync = beat_sync or self.beats[100][key]
        value_sync = value_sync / len(keys)
        
        self.value_sync = value_sync
        self.value = value_sync
        self.beat = beat_sync
        
        for key in keys:
            value_async += self.values[self.activePercent][key]
            beat_async = beat_async or self.beats[self.activePercent][key]
        value_async = value_async / len(keys)
        
        now = time()
        key = long(now * 1000000.0)
        
        if self.asynchronous:
            # Asynchronous
            
            self.value_async = value_async
            self.value = value_async
            self.beat = beat_async
            
            self.plotSync[key] = value_sync
            self.plotAsync[key] = value_async
            self.plotBeats[key] = beat_async
            self.plotOrderedKeys.append(key)
            
        else:
            # Synchronous
            
            self.plotSync[key] = value_sync
            self.plotAsync[key] = value_async
            self.plotBeats[key] = beat_sync
            self.plotOrderedKeys.append(key)
        
        #Set the final value and beat (after first beat and according to latency)
        if self.latency > 0.0:
            if self.asynchronous and (self.bpm[self.activePercent].getAverage() > 0.0):
                period = 60.0/self.bpm[self.activePercent].getAverage()
                self.value = self.getValue(self.plotAsync, now - period + self.latency)
                self.beat = self.getValue(self.plotBeats, now - period + self.latency)
            elif (not self.asynchronous) and (self.bpm[100].getAverage() > 0.0):
                period = 60.0/self.bpm[100].getAverage()
                self.value = self.getValue(self.plotSync, now - period + self.latency)
                self.beat = self.getValue(self.plotBeats, now - period + self.latency)
                
        if self.beat:
            self.lastX = 0.0
        else :
            if (self.lastX < math.pi) :
                self.lastX += dt/self.alphaDuration*math.pi
                self.alphaGlow = math.sin(self.lastX)
            else:
                self.alphaGlow = 0.0
        self.plotAlpha[key] = self.alphaGlow
        
        # Make sure time order is kept
        if (len(self.plotOrderedKeys) > 2) and (self.plotOrderedKeys[-1] < self.plotOrderedKeys[-2]):
            self.plotOrderedKeys = sorted(self.plotOrderedKeys)
    
        # Remove every value with an earlier key than max_duration ago 
        while self.plotOrderedKeys[0] < (key - long((self.maxTime + 1) *1000000.0)):
            if self.plotSync.has_key(self.plotOrderedKeys[0]):
                self.plotSync.pop(self.plotOrderedKeys[0])
                self.plotAsync.pop(self.plotOrderedKeys[0])
                self.plotBeats.pop(self.plotOrderedKeys[0])
                self.plotAlpha.pop(self.plotOrderedKeys[0])
                self.plotOrderedKeys.pop(0)
        
        # Fill in logs if required
        if self.logActive:
            # Log time
            line = [str("%.4f"%self.controller.gTimeManager.experimentTime()), self.controller._currentRoutine, self.controller._currentCondition]
            # Log info
            line.extend([value_sync, beat_sync * self.bpm[100].getAverage(), value_async, beat_async * self.bpm[self.activePercent].getAverage(), self.value, str("%d"%self.beat), self.alphaGlow])
            self.csvLogger.writerow(line)

    def getValue(self, valuestack, time = None):
        if len(valuestack)<1:
            return 0.0;
        # if no time is given or only one elements in the buffer
        # return the last element
        if (time is None) or (len(self.plotOrderedKeys) < 2):
            return valuestack[self.plotOrderedKeys[-1]]
        # if the time given is in the future 
        # return the last element
        keytime = long(time * 1000000.0)
        if (keytime > self.plotOrderedKeys[-1]):
            return valuestack[self.plotOrderedKeys[-1]]
        # if time given is before the first value, return the first value
        if (keytime < self.plotOrderedKeys[0]):
            return valuestack[self.plotOrderedKeys[0]]
        # maybe lucky to have the exact key
        if self.plotOrderedKeys.count(keytime):
            return valuestack[keytime]
        # otherwise find the time asked between the past key times
        low_keytime = keytime
        index = -1
        while self.plotOrderedKeys[index] - keytime > 1:
            index -= 1
        low_keytime = self.plotOrderedKeys[index]
        # get the next key time
        high_keytime = self.plotOrderedKeys[index+1]
        # linear interpolation
        div = high_keytime - low_keytime
        if div != 0:
            return valuestack[low_keytime] + float(keytime - low_keytime) * float(valuestack[high_keytime] - valuestack[low_keytime] ) / float(div) 
        else:
            return valuestack[high_keytime]
            
    def start(self, dt= 0, duration= -1, configName= None):
        DrawableHUDSourceModule.start(self, dt, duration, configName)
            
        self.asynchronous = self.activeConf['asynchronous']
        self.async_percent = self.activeConf['asynchrony_percent']/100.0
        self.activePercent = int(self.activeConf['asynchrony_percent'])
        self.alphaDuration = self.activeConf['alphaGlowDuration']/1000.0
        self.debug = self.activeConf['displayDebug']
        self.latency  = self.activeConf['ECG_BVP_latency']/1000.0
        
        self.lastKey = 0.0
        self.lastX = math.pi + 1.0
        self.alphaGlow = 0.0
        self.value = 0.0
        self.value_sync = 0.0
        self.value_async = 0.0
        self.beat = False
        
        # Plot data
        self.plotAlpha = {}
        self.plotSync = {}
        self.plotAsync = {}
        self.plotBeats = {}
        self.plotOrderedKeys = []
        
        pyglet.clock.schedule(self.update) 
    
    def stop(self, dt= 0):
        DrawableHUDSourceModule.stop(self, dt)
        pyglet.clock.unschedule(self.update)
        
    def cleanup(self):
        DrawableHUDSourceModule.cleanup(self)
        
        pyglet.clock.unschedule(self.update)
        # Close the sensor and wait for the thread to terminate
        self.lock.acquire()
        self.sensor.close()
        del self.sensor
        self.sensor = None
        self.lock.release()
        self.thread.join(1.0)
        self.log('BVP sensor closed.')
            
    def getAlphaGlow(self) :
        return self.alphaGlow

    def getData(self):
        DrawableHUDSourceModule.getData(self)
        return self.value

    def getUpdateInterval(self):
        return DrawableHUDSourceModule.getUpdateInterval(self)