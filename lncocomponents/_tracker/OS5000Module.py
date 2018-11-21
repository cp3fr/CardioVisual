'''
Created on Jan 6, 2011

@author: bh
@since: winter 2010

@license: Distributed under the terms of the GNU General Public License (GPL).
'''

from os import path
import csv
import threading, time

from datetime import datetime
from pyglet.gl import *

#pylnco modules
from display.tools import *
from abstract.AbstractClasses import DrawableSourceModule
from tracker.OS5000 import OS5000
from display.objloader import OBJ

import numpy as np
from tracker.kalman import KalmanTracking

class OSUpdateThread ( threading.Thread ):
    def __init__(self, parent = None):
        threading.Thread.__init__(self)
        self.module = parent
        
    def run(self):
        # front/back sensor data buffer mechanism: if thread writes in front buffer
        # the module will read the back, and conversely
        while True:
            # get the front lock for the thread
            self.module.lockFront.acquire()
            # read data
            if self.module.OSsensor is not None:
                self.module.sensordataFront = self.module.OSsensor.readData()
            else:
                break
            # free the front lock for the module
            self.module.lockFront.release()
            # necessary to give the main thread time to acquire lock
            time.sleep(0)
            # get the back lock for the thread
            self.module.lockBack.acquire()
            # read data
            if self.module.OSsensor is not None:
                self.module.sensordataBack = self.module.OSsensor.readData()
            else:
                break
            # free the back lock for the module
            self.module.lockBack.release()

            
class ModuleMain(DrawableSourceModule):
    """
    A simple module to read data from Ocean Server 3 axis digital compas 
    OS5000 USB kit ; http://www.oceanserver-store.com/osevkitsorus.html
    """
    defaultInitConf = {
        'name': 'OSsensor',
        'port': 'COM3',
        'baudrate': 115200,
        'logToCSV': True,
        'kalmanFilter': False,
        'calibrationKey': 'C'
    }
    
    defaultRunConf = {
        'mirror': False,
        'autoCalibration': True,
        'delay': 0.0
    }
    
    confDescription = [
        ('name', 'str', "Your Ocean Server tracker"),
        ('port', 'str', "Computer port where sensor is plugged", ['COM1', 'COM2', 'COM3', 'COM4','COM5', 'COM6', 'COM7', 'COM8','COM9', 'COM10', 'COM11', 'COM12']),
        ('baudrate', 'int', "Baudrate of connection"),
        ('logToCSV', 'bool', "Save data to coma-separated-values file ( <modulename>_<date>.csv )"),
        ('kalmanFilter', 'bool', "Whether to use Kalman filtering on the sensor data"),  
        ('calibrationKey', 'str', "List of keys which trigger sensor calibration (space-separated list of keys, e.g. 'A B C ENTER')"),
        ('mirror', 'bool', "Flip horizontally (mirror)"),    
        ('delay', 'float', "Delay in second"),  
        ('autoCalibration', 'bool', "Automatically re-calibrate the sensor each time it is activated"),
        ('angles', 'info', "Euler angles (list of floats) of the sensor orientation."),
    ]
    
    def __init__(self, controller, initConfig=None, runConfigs=None):
        DrawableSourceModule.__init__(self, controller, initConfig, runConfigs)
                
        # init file
        self.logActive = self.initConf['logToCSV']
        if self.logActive:
            now = datetime.today()
            self.csvLogger = csv.writer(open(path.join(self.controller.gLogger.Path, now.strftime('%y%m%d%H%M%S_') + self.initConf['name'] +  '.csv') , 'w'), lineterminator = '\n')

        self.controller.registerKeyboardAction( self.initConf['calibrationKey'], self.calibrate )
        
        # init sensor
        self.angles = [0.0, 0.0, 0.0]
        self.OSsensor = OS5000(port=self.initConf['port'], baudrate=self.initConf['baudrate'])
        self.mesh = OBJ("..\\..\\\\resources\\data\\icosahedron.obj")
        
        # init delay buffer
        self.data = []
        self.maxdelay = 0.0
        self.updateTime = 0.02 # 50Hz
        self.writeIndex = 0
        self.frameDelay = 0
        # READ MAX DELAY FROM RUN CONFIGS
        for conf in self.runConfs.values():
            if conf['delay'] > self.maxdelay:
                self.maxdelay = conf['delay']
        # compute max frame delay (size of delay buffer) and initialize it
        self.maxFrameDelay = int (self.maxdelay / self.updateTime)
        for i in xrange(self.maxFrameDelay + 1):             
            self.data.insert( i, np.zeros(3) )
        
        # setup filtering
        if self.initConf['kalmanFilter']:
            self.kalmanTracker = KalmanTracking(3, [0.1, 0.1, 0.2], 0.015, self.updateTime)
        else:
            self.kalmanTracker = None
        
        # create and start thread
        self.lockFront = threading.Lock()
        self.lockBack = threading.Lock()
        self.thread = OSUpdateThread(parent=self)
        self.thread.start()
            
    def draw(self, window_width, window_height, eye=-1):
        DrawableSourceModule.draw(self, window_width, window_height, eye)

        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glLightfv(GL_LIGHT0, GL_POSITION, vec4f([0.0, 0.0, 12.0, 0.0]))
        glLightfv(GL_LIGHT0, GL_AMBIENT, vecf(.03, .03, .03, 1))
        glLightfv(GL_LIGHT0, GL_DIFFUSE, vecf(.5, .5, .5, 1))
        glLightfv(GL_LIGHT0, GL_SPECULAR, vecf(.05, .05, .05, 1))
        
        ## display SENSOR orientation
        glTranslatef(0.0, 0.0, -3.0)
        glRotatef(self.angles[0],1,0,0)
        glRotatef(self.angles[1],0,1,0)
        glRotatef(self.angles[2],0,0,1)
        glCallList(self.mesh.gl_list)

        glDisable(GL_LIGHTING)
            
    def start(self, dt=0, duration=-1, configName=None):
        """
        Activate the optic flow engine with the parameters passed in the conf
        """
        DrawableSourceModule.start(self, dt, duration, configName)
            
        self.angles = [0.0, 0.0, 0.0]
        self.sensordataFront = np.zeros(3)
        self.sensordataBack = np.zeros(3)
        self.calibrationdata = np.zeros(3)
        self.wasUpdated = False
        
        if self.activeConf['autoCalibration']:
            self.calibrate()
        
        # setup delay and start updating
        self.frameDelay = int ( self.activeConf['delay'] / self.updateTime )
        pyglet.clock.schedule_interval(self.update, self.updateTime)  # > 32Hz
#        pyglet.clock.schedule(self.update)

    def stop(self, dt=0):
        DrawableSourceModule.stop(self, dt)
        pyglet.clock.unschedule(self.update)
        
    def cleanup(self):
        DrawableSourceModule.cleanup(self)
        self.controller.unregisterKeyboardAction( self.initConf['calibrationKey'], self.calibrate )
        
        # request stop and wait for the thread to terminate
        self.lockFront.acquire()
        self.OSsensor = None
        self.lockFront.release()
        self.thread.join(1.0)
        
    def setAnglesFromData(self, data):
        # use the next index to write into
        self.writeIndex = (self.writeIndex + 1) % (self.maxFrameDelay + 1)
        # read data from thread and immediately let it continue
        if self.kalmanTracker is None:
            self.data[self.writeIndex] = data - self.calibrationdata
        else:
            self.kalmanTracker.observe(data)
            self.data[self.writeIndex] = self.kalmanTracker.X - self.calibrationdata
            self.kalmanTracker.predict()
        # set index for reading the former data
        readIndex = (self.writeIndex - self.frameDelay) % (self.maxFrameDelay + 1)
        # fill in the angle array from data reading index          
        if np.isreal(self.data[readIndex]).all():
            self.angles[0] = self.data[readIndex][1]
            self.angles[1] = -self.data[readIndex][0] 
            self.angles[2] = -self.data[readIndex][2]
        
    def update(self, dt):
        """
        The update is called regularly to update angle data
        """
        # get the data with front/back sensor data buffer mechanism: if thread writes in front buffer
        # the module will read the back, and conversely
        if (self.lockFront.acquire(False)):
            self.setAnglesFromData(self.sensordataFront)
            self.lockFront.release()
        elif (self.lockBack.acquire(False)):    
            self.setAnglesFromData(self.sensordataBack)
            self.lockBack.release()
        
        if self.activeConf['mirror']:
            self.angles[1] = -self.angles[1]
            self.angles[0] = -self.angles[0]
            
        if self.logActive:
            # log time
            line = [ str("%.4f"%self.controller.gTimeManager.experimentTime()), self.controller._currentRoutine, self.controller._currentCondition  ]
            # log coordinates
            line.extend(self.angles)
            self.csvLogger.writerow(line)

    def calibrate(self, key = None):
        """
        Perform calibration by remembering current sensor values
        """
        if (key != None):
            self.log("User calibration requested")
        if self.lockFront.acquire():
            self.calibrationdata = np.array(self.sensordataFront)
            self.lockFront.release()


    def getData(self):
        """
        For abstract interface (reactor is a source module). Keeping getPositions() for old calls to positions
        """
        DrawableSourceModule.getData(self)
        return self.angles

    def getUpdateInterval(self):
        """
        For abstract interface (reactor is a source module). 
        """
        return self.updateTime
