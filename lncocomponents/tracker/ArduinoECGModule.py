'''
Created on Mar 15, 2013

@author: Javier Bello Ruiz
@since:  Spring 2013

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

    def __init__(self, *args, **kwargs):
        # Ensure that a reasonable timeout is set
        timeout = kwargs.get('timeout', 0.1)
        if timeout < 0.01: timeout = 0.1
        kwargs['timeout'] = timeout
        serial.Serial.__init__(self, *args, **kwargs)
        
    def readData(self, timeout= 1):
        try:
            # Read sensor data and extract values
            self.buf = self.readline()
        except:
            self.buf = ''
        if (len(self.buf) < 4) or (self.buf[0] != '[') or (self.buf.count(']') < 1):
            return [0.0, 0, 0.0, 0.0]
        data = re.split('[\[,\]]', self.buf)
        self.buf = ''
        try :
            list = [float(f) for f in data[1:-1]]
        except:
            list = [0.0, 0, 0.0, 0.0]
        if len(list) < 4: list = [0.0, 0, 0.0, 0.0] 
        return list
        
class arduinoUpdateThread (threading.Thread):

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
                # Detect contiguous peaks for bpm
                beat = bool(measure[1])
                period = 0.0
                if (self.module.bpmtime[100] < 0.0) : self.module.bpmtime[100] = now
                if beat:
                    period = now - self.module.bpmtime[100]
                    self.module.bpmtime[100] = now
                    # Peak detected in a reasonable time period
                    if (period > 0.4) and (period < 1.2):
                        beat = True
                        self.module.bpm[100].appendValue(now, 60.0/period)
                    else: beat = False
                
                key = long(now*1000000.0)
                self.module.values[100][key] = measure[0]
                self.module.beats[100][key] = beat
                self.module.mins[100][key] =  measure[2]
                self.module.maxs[100][key] = measure[3]
                self.module.orderedKeys.append(key)
                
                if (self.module.previousTime < 0.0) : self.module.previousTime = now
                dt = now - self.module.previousTime
                self.module.previousTime = now
                
                if self.module.logActive:
                    # Log ECG signal
                    row = [str("%.6f"%dt), str("%.6f"%measure[0]), str("%d"%beat), str("%.6f"%measure[2]), str("%.6f"%measure[3])]
                    self.module.csvECG.writerow(row)
#######################################################################################################################################
                for percentage in self.module.percentages:
                    
                    self.module.mulFactor[percentage] = (float(percentage)/100.0 * self.module.bpm[100].getAverage()) / self.module.template_bpm
                     # Asynchronous: apply multiplying factor to speed up or slow down playing of the template
                    auxdt = dt * self.module.mulFactor[percentage]
                    # Start detection of next time with previous error in dt
                    t = self.module.t_error[percentage]
                    
                    value_async = 0.0
                    beat_async = False
                    min_async = 0.0
                    max_async = 0.0
                    
                    # While the t is before the dt we want
                    while t < auxdt:
                        # To find the index in template timings
                        self.module.index[percentage] = (self.module.index[percentage] + 1)%len(self.module.template)
                        t += self.module.template[self.module.index[percentage]][0]
                        beat_async = bool(self.module.template[self.module.index[percentage]][2]) or beat_async
                    
                    # We passed the dt by t-dt
                    self.module.t_error[percentage] = t - auxdt
                    
                    # Interpolate linearly between the values
                    if self.module.template[self.module.index[percentage]][0] == 0:
                        percent = self.module.t_error[percentage] 
                    else:
                        percent = self.module.t_error[percentage]  / self.module.template[self.module.index[percentage]][0]

                    value_async = percent * self.module.template[self.module.index[percentage]][1] + (1.0 - percent) * self.module.template[self.module.index[percentage] - 1][1]
                    min_async = percent * self.module.template[self.module.index[percentage]][3] + (1.0 - percent) * self.module.template[self.module.index[percentage] - 1][3]
                    max_async = percent * self.module.template[self.module.index[percentage]][4] + (1.0 - percent) * self.module.template[self.module.index[percentage] - 1][4]

########################################################################################################################################
                    period = 0.0
                    if (self.module.bpmtime[percentage] < 0.0) : self.module.bpmtime[percentage] = now
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
                    self.module.mins[percentage][key] =  min_async
                    self.module.maxs[percentage][key] = max_async
                    
                    if self.module.logActive:
                        # Log ECG async signal
                        row = [str("%.6f"%dt), str("%.6f"%value_async), str("%d"%beat_async), str("%.6f"%min_async), str("%.6f"%max_async)]
                        self.module.csvAsyncECG[percentage].writerow(row)
                    
                # Make sure time order is kept
                if (len(self.module.orderedKeys) > 2) and (self.module.orderedKeys[-1] < self.module.orderedKeys[-2]):
                    self.module.orderedKeys = sorted(self.module.orderedKeys)
                # Remove every value with an earlier key than max_duration ago 
                while self.module.orderedKeys[0] < (key - long((self.module.maxTime + 1)*1000000.0)):
                    if self.module.values[100].has_key(self.module.orderedKeys[0]):
                        self.module.values[100].pop(self.module.orderedKeys[0])
                        self.module.beats[100].pop(self.module.orderedKeys[0])
                        self.module.mins[100].pop(self.module.orderedKeys[0])
                        self.module.maxs[100].pop(self.module.orderedKeys[0])
                        for percentage in self.module.percentages:
                            self.module.values[percentage].pop(self.module.orderedKeys[0])
                            self.module.beats[percentage].pop(self.module.orderedKeys[0])
                            self.module.mins[percentage].pop(self.module.orderedKeys[0])
                            self.module.maxs[percentage].pop(self.module.orderedKeys[0])
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
        'name': 'ECG',
        'port': 'COM4',
        'baudrate' : 115200,
        'logToCSV': True
    }
    
    defaultRunConf = {
        'asynchronous': False,
        'asynchrony_percent': 80,
        'displayDebug': False,
        'alphaGlowDuration': 500,
        'alphaGlowPhaseShifted': False
    }
    
    confDescription = [
        ('name', 'str', "Your ECG tracker."),
        ('port', 'str', "Computer port where sensor is plugged", ['COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'COM10', 'COM11', 'COM12']),
        ('baudrate', 'int', "Connection baud rate."),
        ('logToCSV', 'bool', "Save data to coma-separated-values file (<date>_<modulename>.csv)."),
        ('asynchronous', 'bool', "Display in asynchronous way."),
        ('asynchrony_percent', 'int', "Percent of heart beat frequency to display asynchronously (e.g. 80, or 120)."),
        ('displayDebug', 'bool', "Display the debug signal (opposite condition to current)."),
        ('alphaGlowDuration', 'int', "Duration of the alpha glow animation in ms."),
        ('alphaGlowPhaseShifted', 'bool', "Alpha glow animation is displayed with a phase shift of half of the time between two beats."),
        ('getData()', 'info', "Value synchronous or asynchronous of the ECG signal."),
        ('getAlphaGlow()', 'info', "Value to display the alpha glow [0.0, 1.0]"),
        ('beat', 'info', "Synchronous or asynchronous beat(binary value: 0 or 1)."),
        ('realHeartbeat', 'info', "Real heartbeat of the subject for trigger purposes.")
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
        self.lastY = math.pi + 1.0
        self.lastZ = math.pi + 1.0
        self.alphaGlow = 0.0
        self.alphaGlowShifted = 0.0
        self.async_percent = 80.0
        self.value = 0.0
        self.value_sync = 0.0
        self.value_async = 0.0
        self.beat = False
        self.realHeartbeat = False
        
        # Plot data
        self.plotAlpha = {}
        self.plotAlphaShifted = {}
        self.plotSync = {}
        self.plotAsync = {}
        self.plotBeats = {}
        self.plotMins = {}
        self.plotMaxs = {}
        self.plotOrderedKeys = []
        
        # Dictionaries
        self.values = {}
        self.beats = {}
        self.mins = {}
        self.maxs = {}
        self.bpm = {}
        self.bpmtime = {}
        self.mulFactor = {}
        self.t_error = {}
        self.index = {}
        
        self.percentages = []
        self.orderedKeys = []
        self.previousTime = -1.0
        
        # Sync
        self.values[100] = {}
        self.beats[100] = {}
        self.mins[100] = {}
        self.maxs[100] = {}
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
            self.csvECG = csv.writer(open(path.join(self.controller.gLogger.Path, now.strftime('%y%m%d%H%M%S_') + 'ECGsignal' +  '.csv') , 'w'), lineterminator = '\n')
            line = ['exp_time', 'Routine', 'Condition', 'sync_value', 'sync_beat(bpm)', 'async_value', 'async_beat(bpm)', 'display_value', 'display_beat', 'alphaGlow_value']
            self.csvLogger.writerow(line)
        
        # Async
        self.csvAsyncECG = {}
        for conf in self.runConfs.values():
            percentage = int(conf['asynchrony_percent'])
            if (percentage in self.percentages) or (percentage == 100):
                continue
            self.percentages.append(percentage)
            self.values[percentage] = {}
            self.beats[percentage] = {}
            self.mins[percentage] = {}
            self.maxs[percentage] = {}
            self.bpm[percentage] = BufferBox(20.0)
            self.bpmtime[percentage] = -1.0
            self.mulFactor[percentage] = 0.0
            self.t_error[percentage] = 0.0
            self.index[percentage] = -1
            self.csvAsyncECG[percentage] = csv.writer(open(path.join(self.controller.gLogger.Path, now.strftime('%y%m%d%H%M%S_') + 'ECGasync' + str(percentage) + '.csv') , 'w'), lineterminator = '\n')
                    
        # Load template data
        filename = path.join(path.dirname(__file__), "ECG_template_javier_68bpm.csv")
        templatereader = csv.reader(open(filename))
        for l in templatereader:
            self.template.append([float(l[0]), float(l[1]), float(l[2]), float(l[3]), float(l[4])])
        # Template data average frequency (BPM)
        self.template_bpm = 67.722
        
        # Initialize sensor
        self.sensor = Arduino(port=self.initConf['port'], baudrate=115200)
        self.log('ECG sensor opened.')

        # Create and start the reading thread
        self.lock = threading.Lock()
        self.thread = arduinoUpdateThread(parent=self)
        self.thread.start()
        
        timeout = 0.0
        print "Starting ECG module",
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
        
        """
        glColor4f(0, 1, 0, 1)
        glBegin(GL_LINE_LOOP)
        glVertex2f(-50, -1)
        glVertex2f(-50, window_height/2)
        for key in self.plotOrderedKeys:
            t = now - float(key)/1000000.0
            y = self.plotMins[key] / 3.0
            glVertex2f(window_width * (self.maxTime - t)/self.maxTime, y * window_height)
        glVertex2f(window_width + 50, -1)
        glEnd()
        
        glColor4f(0, 1, 0, 1)
        glBegin(GL_LINE_LOOP)
        glVertex2f(-50, -1)
        glVertex2f(-50, window_height/2)
        for key in self.plotOrderedKeys:
            t = now - float(key)/1000000.0
            y = self.plotMaxs[key] / 3.0
            glVertex2f(window_width * (self.maxTime - t)/self.maxTime, y * window_height)
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
        
        glColor4f(0, 1, 0, 1)
        glBegin(GL_LINE_LOOP)
        glVertex2f(-50, -1)
        glVertex2f(-50, window_height/2)
        for key in self.plotOrderedKeys:
            t = now - float(key)/1000000.0
            y = self.plotAlphaShifted[key]
            glVertex2f(window_width * (self.maxTime - t)/self.maxTime, y * window_height)
        glVertex2f(window_width + 50, -1)
        glEnd()
        """
        
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
        The update is called regularly to update data
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
        min_sync = 0.0
        max_sync = 0.0
        
        value_async = 0.0
        beat_async = False
        min_async = 0.0
        max_async = 0.0
                    
        for key in keys:
            value_sync += self.values[100][key]
            beat_sync = beat_sync or self.beats[100][key]
            min_sync += self.mins[100][key]
            max_sync += self.maxs[100][key]
        value_sync = value_sync / len(keys)
        min_sync = min_sync / len(keys)
        max_sync = max_sync / len(keys)
        
        self.value_sync = value_sync
        self.value = value_sync
        self.beat = beat_sync
        self.realHeartbeat = beat_sync
        
        for key in keys:
            value_async += self.values[self.activePercent][key]
            beat_async = beat_async or self.beats[self.activePercent][key]
            min_async += self.mins[self.activePercent][key]
            max_async += self.maxs[self.activePercent][key]
        value_async = value_async / len(keys)
        min_async = min_async / len(keys)
        max_async = max_async / len(keys)
        
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
            self.plotMins[key] = min_async
            self.plotMaxs[key] = max_async
            self.plotOrderedKeys.append(key)
        
        else:
            # Synchronous
            
            self.plotSync[key] = value_sync
            self.plotAsync[key] = value_async
            self.plotBeats[key] = beat_sync
            self.plotMins[key] = min_sync
            self.plotMaxs[key] = max_sync
            self.plotOrderedKeys.append(key)
        
        if self.beat:
            self.lastX = 0.0
        else :
            if (self.lastX < math.pi) :
                self.lastX += dt/self.alphaDuration*math.pi
                self.alphaGlow = math.sin(self.lastX)
            else:
                self.alphaGlow = 0.0
        self.plotAlpha[key] = self.alphaGlow
        
        delay = 0.25
        if self.asynchronous:
            if (self.bpm[self.activePercent].getAverage() > 0.0):
                delay  = 30.0 / self.bpm[self.activePercent].getAverage()
        else:
            if (self.bpm[100].getAverage() > 0.0):
                delay = 30.0 / self.bpm[100].getAverage()

        beatShifted = False
        if self.beat:
            self.lastY = 0.0
        else :
            if (self.lastY < 1.0):
                self.lastY += dt/delay
            elif (self.lastY != (math.pi + 1)):
                beatShifted = True
                self.lastY = math.pi + 1
        
        if beatShifted:
            self.lastZ = 0.0
        else :
            if (self.lastZ < math.pi) :
                self.lastZ += dt/self.alphaDuration*math.pi
                self.alphaGlowShifted = math.sin(self.lastZ)
            else:
                self.alphaGlowShifted = 0.0
        self.plotAlphaShifted[key] = self.alphaGlowShifted
        
        if self.alphaShifted:
            self.alphaGlow = self.alphaGlowShifted
                              
        # Make sure time order is kept
        if (len(self.plotOrderedKeys) > 2) and (self.plotOrderedKeys[-1] < self.plotOrderedKeys[-2]):
            self.plotOrderedKeys = sorted(self.plotOrderedKeys)
    
        # Remove every value with an earlier key than max_duration ago 
        while self.plotOrderedKeys[0] < (key - long((self.maxTime + 1) *1000000.0)):
            if self.plotSync.has_key(self.plotOrderedKeys[0]):
                self.plotSync.pop(self.plotOrderedKeys[0])
                self.plotAsync.pop(self.plotOrderedKeys[0])
                self.plotBeats.pop(self.plotOrderedKeys[0])
                self.plotMins.pop(self.plotOrderedKeys[0])
                self.plotMaxs.pop(self.plotOrderedKeys[0])
                self.plotAlpha.pop(self.plotOrderedKeys[0])
                self.plotAlphaShifted.pop(self.plotOrderedKeys[0])
                self.plotOrderedKeys.pop(0)
        
        # Fill in logs if required
        if self.logActive:
            # Log time
            line = [str("%.4f"%self.controller.gTimeManager.experimentTime()), self.controller._currentRoutine, self.controller._currentCondition]
            # Log info
            line.extend([value_sync, beat_sync * self.bpm[100].getAverage(), value_async, beat_async * self.bpm[self.activePercent].getAverage(), self.value, str("%d"%self.beat), self.alphaGlow])
            self.csvLogger.writerow(line)
    
    def start(self, dt= 0, duration= -1, configName= None):
        DrawableHUDSourceModule.start(self, dt, duration, configName)
        
        self.asynchronous = self.activeConf['asynchronous']
        self.async_percent = self.activeConf['asynchrony_percent']/100.0
        self.activePercent = int(self.activeConf['asynchrony_percent'])
        self.alphaDuration = self.activeConf['alphaGlowDuration']/1000.0
        self.alphaShifted = self.activeConf['alphaGlowPhaseShifted']
        self.debug = self.activeConf['displayDebug']
        
        self.lastKey = 0.0 # should be long(0.0) * 1000000.0?
        self.lastX = math.pi + 1.0
        self.lastY = math.pi + 1.0
        self.lastZ = math.pi + 1.0
        self.alphaGlow = 0.0
        self.alphaGlowShifted = 0.0
        self.value = 0.0
        self.value_sync = 0.0
        self.value_async = 0.0
        self.beat = False
        self.realHeartbeat = False
        
        # Plot data
        self.plotAlpha = {}
        self.plotAlphaShifted = {}
        self.plotSync = {}
        self.plotAsync = {}
        self.plotBeats = {}
        self.plotMins = {}
        self.plotMaxs = {}
        self.plotOrderedKeys = []
        
        pyglet.clock.schedule(self.update)
        
    def startMassiveAsync(self, asynchrony_percent):
        
        self.asynchronous = True
        self.async_percent = asynchrony_percent/100.0
        self.activePercent = int(asynchrony_percent)
        self.alphaDuration = self.activeConf['alphaGlowDuration']/1000.0
        self.alphaShifted = self.activeConf['alphaGlowPhaseShifted']
        self.debug = self.activeConf['displayDebug']
        
        self.lastKey = 0.0 # should be long(0.0) * 1000000.0?
        self.lastX = math.pi + 1.0
        self.lastY = math.pi + 1.0
        self.lastZ = math.pi + 1.0
        self.alphaGlow = 0.0
        self.alphaGlowShifted = 0.0
        self.value = 0.0
        self.value_sync = 0.0
        self.value_async = 0.0
        self.beat = False
        self.realHeartbeat = False
        
        # Plot data
        self.plotAlpha = {}
        self.plotAlphaShifted = {}
        self.plotSync = {}
        self.plotAsync = {}
        self.plotBeats = {}
        self.plotMins = {}
        self.plotMaxs = {}
        self.plotOrderedKeys = []
        
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
        self.log('ECG sensor closed.')
        
    def getAlphaGlow(self) :
        return self.alphaGlow
                    
    def getData(self):
        DrawableHUDSourceModule.getData(self)
        return self.value

    def getUpdateInterval(self):
        return DrawableHUDSourceModule.getUpdateInterval(self)
        
"""
#include <eHealth.h>

#define SENSITIVITY 0.8

float ECG, previousECG;
float EMA_ECG, EMA_MIN_ECG, EMA_MAX_ECG;
float EMA_alpha_ECG, EMA_alpha_extrema;
const int led = 13;
boolean beat = false;

// The setup routine runs once when you press reset:
void setup() {
  pinMode(led, OUTPUT); 
  
  ECG = eHealth.getECG();
  EMA_ECG = ECG;
  EMA_MIN_ECG = ECG;
  EMA_MAX_ECG = ECG;
  EMA_alpha_ECG = 2.0 / (2.0 + 1.0);
  EMA_alpha_extrema = 2.0 / (50.0 + 1.0);
  
  Serial.begin(115200);
}

void loop() {
  beat = false;  
  previousECG = ECG;
  ECG = eHealth.getECG();
   
  EMA_ECG = EMA_alpha_ECG * ECG + (1.0 - EMA_alpha_ECG) * EMA_ECG;

  float ECG_MIN = min(ECG, EMA_MIN_ECG);
  EMA_MIN_ECG = EMA_alpha_extrema * (EMA_ECG*0.1 + ECG_MIN*0.9) + (1.0 - EMA_alpha_extrema) * EMA_MIN_ECG;

  float ECG_MAX = max(ECG, EMA_MAX_ECG);
  EMA_MAX_ECG = EMA_alpha_extrema * (EMA_ECG*0.1 + ECG_MAX*0.9) + (1.0 - EMA_alpha_extrema) * EMA_MAX_ECG;
  
  if (abs(ECG - previousECG) > SENSITIVITY * abs(EMA_MAX_ECG - EMA_MIN_ECG))
    beat = true;
  
  if (beat) digitalWrite(led, HIGH);
  else digitalWrite(led, LOW); 
  
  Serial.print("[");
  Serial.print(EMA_ECG, DEC);
  Serial.print(",");
  Serial.print(beat, DEC);
  Serial.print(",");
  Serial.print(EMA_MIN_ECG, DEC);
  Serial.print(",");
  Serial.print(EMA_MAX_ECG, DEC);
  Serial.println("]");

  delay(10);
}
"""