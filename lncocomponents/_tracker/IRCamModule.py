'''
Interface module for 2-camera stereo object tracking

@author: Nathan Evans
@since April 5, 2011
@license: Distributed under the terms of the GNU General Public License (GPL).
'''

from os import path
import csv
import threading, time

from datetime import datetime
from pyglet.gl import *
import numpy as np
 
#expyvr modules
from display.tools import *
from abstract.AbstractClasses import DrawableSourceModule
from tracker.kalman import KalmanTracking, RigidTrack
from tracker.IRCamInterface import *
from display.objloader import OBJ
from controller import getPathFromString


            
class ModuleMain(DrawableSourceModule):
    """
    Module to extract 2D position from a stereo pair of IR cameras. 
    """
    defaultInitConf = {
        'name': 'IRCam',
        'udpPort': 5555,
        'updateFrequency': 100,
        'kalmanFilter': False,
        'logToCSV': True
    }
    
    defaultRunConf = {
        'delay': 0.0,
        'mirror': False,
        'playbackMode': False,
        'playbackFile': 'playback_filename.csv'
    }
    
    confDescription = [
        ('name', 'str', "Stereo Camera Tracker name"),
        ('udpPort', 'int', "Port for UDP communication"),
        ('updateFrequency', 'float', "Frequency (in Hz) to retrieve the sensor data"),
        ('kalmanFilter', 'bool', "Whether to use Kalman filtering on the sensor data"),
        ('logToCSV', 'bool', "Save data to coma-separated-values file ( <modulename>_<date>.csv )"),
        ('delay', 'float', "Delay (in seconds)"),
        ('mirror', 'bool', "Invert Y rotations"),
        ('playbackMode', 'bool', "Ignore real-time Mocap data and playback pre-recorded sensor data from CSV file"),
        ('playbackFile', 'str', "Full path and filename of the pre-recorded Mocap data (CSV or EMF file) to use"),
        ('rawSensorData', 'info', "Numpy array(2) of marker coordinates (x,y) "),
    ]
    
    def __init__(self, controller, initConfig=None, runConfigs=None):
        DrawableSourceModule.__init__(self, controller, initConfig, runConfigs)
                
        # init 
        self.logActive = self.initConf['logToCSV']
        if self.logActive:
            now = datetime.today()
            self.csvLogger = csv.writer(open(path.join(self.controller.gLogger.Path, now.strftime('%y%m%d%H%M%S_') + self.initConf['name'] +  '.csv') , 'w'), lineterminator = '\n')
        
        # See if we only playback from files
        self.playbackOnly = True
        for conf in self.runConfs.values():
            if not conf['playbackMode']:
                self.playbackOnly = False
                break

        # Pre-load playback mode files (csv reader objects)
        self.playbackFiles = {}
        for conf in self.runConfs.values():
            if conf['playbackMode']:
                pbfile = conf['playbackFile']
                if pbfile not in self.playbackFiles:
                    if pbfile.endswith('.emf'):
                        self.playbackFiles[pbfile] = EMFDataFile(pbfile)
                    else:
                        self.playbackFiles[pbfile] = CSVDataFile(pbfile)
        
        if not self.playbackOnly:        
            self.IRCamInterface = IRCamInterface(self.initConf['udpPort'], "eth0")
            self.IRCamInterface.start()
            
        self.updateInterval = 1.0 / self.initConf['updateFrequency']
        self.rawSensorData = np.zeros(3)      #x-y coords
        self.sensor = Sensor(3, self.updateInterval, enableFilter=self.initConf['kalmanFilter'])
        
  
        # For delayed tracker data
        self.maxdelay = 0.0
        for conf in self.runConfs.values():
            if conf['delay'] > self.maxdelay:
                self.maxdelay = conf['delay']

        self.delaySlots = self.initConf['updateFrequency'] * self.maxdelay
        self.delayBuffer = []
                
        #Visual feedback
        self.sphere = gluNewQuadric()
        gluQuadricNormals(self.sphere, GLU_SMOOTH)
            
    def draw(self, window_width, window_height, eye=-1):
        DrawableSourceModule.draw(self, window_width, window_height, eye)

        glColor3f(1.0,1.0,1.0)  #white
        pos = self.rawSensorData[:]
        glTranslatef(pos[0], 0, pos[1])
        gluSphere(self.sphere,0.2,30,30)
        glTranslatef(-pos[0], 0, -pos[1])
            
    def start(self, dt=0, duration=-1, configName=None):
        """
        Start tracking IR emitter with cameras 
        """
        DrawableSourceModule.start(self, dt, configName)
        
        self._update(0)
            
        # setup delay and start updating
        pyglet.clock.schedule_interval(self._update, self.updateInterval)

    def stop(self, dt=0):
        DrawableSourceModule.stop(self, dt)
        pyglet.clock.unschedule(self._update)
        
    def cleanup(self):
        DrawableSourceModule.cleanup(self)

        #if not self.playbackOnly:
        #    self.IRCam.stopCapture()

        
    def getData(self):
        DrawableSourceModule.getData(self)

        delay = self.activeConf['delay']
        if delay > 0:
            index = int(delay / float(self.updateInterval))
            if len(self.delayBuffer) > index:
                return self.delayBuffer[index]
            else:
                self.log("Delay data requested that is not (yet) available (delay %s). Returning current data instead." % delay)

        positions = self.sensor.getPosition()
        
        #For 2D zero out Z coord -- later can change to 3D if wanted
        positions[2] = 0
            
        return positions
    
    def getUpdateInterval(self):
        DrawableSourceModule.getUpdateInterval(self)
        return self.updateInterval
        
        
    def _update(self, dt):
        """
        The update is called regularly to update current position
        """
        # Get current sample from mocap or pre-rec file
        if not self.activeConf['playbackMode']:
            self.rawSensorData = self.IRCamInterface.getPositions()         
        else:
            self.rawSensorData = self.playbackFiles[self.activeConf['playbackFile']].next()
        
        #in case we have more than 1 channel from feedback file
        if self.rawSensorData.ndim > 1:
            self.rawSensorData = self.rawSensorData[:,1]    

        # update sensors and their filters
        self.sensor.receiveData( self.rawSensorData[:] )
        self.sensor.update()
                
        # store the data as history if needed
        if self.delaySlots > 0:
            if len(self.delayBuffer) >= self.delaySlots:
                self.delayBuffer.pop()
            self.delayBuffer.insert(0, self.getPositions())
                
        # compute mirror if requested
#        if self.activeConf['mirror']:
#            self.angles[1] = -self.angles[1]
#            self.angles[0] = -self.angles[0]
        
        #Only log if we're actively taking mocap input
        if self.logActive and self.activeConf['logToCSV'] and not self.activeConf['playbackMode']:
            # log times and location in experiment flow
            line = [self.controller.gTimeManager.experimentTime(), self.controller._currentRoutine, self.controller._currentCondition]
            # log coordinates
            sensor = self.rawSensorData.transpose().tolist() #local var sensors
            line.extend([coord for coord in sensor])
            self.csvLogger.writerow(line)
                        
            
class Sensor():
    """
    One sensor corresponds to a vectorial source that is supposed to be tracked
    """
    def __init__(self, dimensions, updateInterval, enableFilter=False):
        self.updateInterval = updateInterval
        self.dimensions = dimensions
        self.state = np.zeros(self.dimensions)
        self.filter = enableFilter

        if self.filter:
            # Parameters demand measurements about the noise of the MOCAP system
            self.kalmanTracker = KalmanTracking(self.dimensions, [0.1, 0.1, 0.1], 
                                                0.05, self.updateInterval)

    def getPosition(self):
        if self.filter:
            return self.kalmanTracker.X
        else:
            return self.state

    def getVelocity(self):
        if self.filter:
            return self.kalmanTracker.V
        else:
            return np.zeros(self.dimensions)

    def getAcceleration(self):
        if self.filter:
            return self.kalmanTracker.A
        else:
            return np.zeros(self.dimensions)

    #This MUST be called every self.updateInterval seconds
    def update(self):
        if self.filter:
            self.kalmanTracker.predict()
            self.state = self.kalmanTracker.X.copy()
            
    def receiveData(self, data):
        if self.filter:
            self.kalmanTracker.observe(data)
            self.state = self.kalmanTracker.X.copy()
        else:
            self.state = data.copy()
            
class CSVDataFile(object):
    """
    A wrapper to playback reactor data that was stored by ExpyVR to a csv file
    """
    def __init__(self, filename):
        self.file = csv.reader(open(getPathFromString(filename),'rb'))
    
    def next(self):
        try:
            curSample = self.file.next()      #grab next row
        except StopIteration:
            return np.zeros(3)       #@todo - if we run out of samples in file could re-iterate. now set to zeros
        tmp = np.array(curSample[1:],dtype=np.float64)  #skip timestamp
        return tmp.reshape(3, tmp.shape[0]/3) #reshape timestep to matrix


    
class EMFDataFile(object):
    """
    A wrapper to playback reactor data that was stored as an emf file
    """
    def __init__(self, filename):
        self.samples = []
        self.sampleNum = 0
        
        emfFile = open(getPathFromString(filename))
        sample = EMFDataFile.__parseSample(emfFile)
        while not sample == None:
            self.samples.append(sample)
            sample = EMFDataFile.__parseSample(emfFile)
        emfFile.close()
    
    def next(self):
        data = self.samples[self.sampleNum].copy()
        self.sampleNum += 1
        if self.sampleNum >= len(self.samples):
            self.sampleNum = 0
        return data
        
    @staticmethod
    def __parseSample(file):
        """
        Reads one sample from the emf file
        """
        # Hack, hack, hack...
        line = ''
        sample = np.zeros((3, 30))
        while not line.startswith(':Sample'):
            line = file.readline()
            if len(line) == 0:
                return None
        line = file.readline()
        i = 0
        while len(line) > 2:
            vals = [float(num)/1000 for num in line.split()]
            sample[:,i] = vals[1:]
            i += 1
            line = file.readline()
        return sample
        