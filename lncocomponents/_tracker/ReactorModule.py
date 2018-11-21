'''
Read or playback (pre-recorded file) motion capture data from a Reactor mocap system

@author: bh, Danilo, Tobias Leugger, Nathan
@since: Summer 2010

'''

from os import path
import numpy as np
import csv
import math
from datetime import datetime
from pyglet.gl import *

#pylnco modules
from abstract.AbstractClasses import DrawableSourceModule
from tracker.kalman import KalmanTracking, RigidTrack
import tracker.ReactorHandler as ReactorHandler
from controller import getPathFromString


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



class ModuleMain(DrawableSourceModule):
    """
    A simple module to log the data from Reactor Motion capture into CSV file
    (and also log key press as triggers)
    """
    defaultInitConf = {
        'name': 'reactor',
        'IP': '192.168.0.7',
        'nb_sensors': 30,
        'updateFrequency': 30,
        'cameraPositionSensors': '0,1,2,3',
        'calibrationKey': 'C',
        'kalmanFilter': False,
        'dataHistoryTime': 0.0,
    }
    
    defaultRunConf = {
        'autoCalibration': False,
        'playbackMode': False,
        'playbackFile': 'playback_filename.csv',
        'logToCSV': True,
    }
    
    confDescription = [
        ('name', 'str', "Fusion Core Reactor mocap"),
        ('IP', 'str', "IP address of the computer running Reactor server (port 6001 is assumed). Leave empty all conditions are only playback"),
        ('nb_sensors', 'int', "Number of sensors to read"),
        ('logToCSV', 'bool', "Save raw sensor data to coma-separated-values file ( <modulename>_<date>.csv )"),
        ('updateFrequency', 'float', "Frequency (in Hz) to retrieve the sensor data"),
        ('cameraPositionSensors', 'str', 'Comma separated list of sensors to use for tracking the head position. Leave empty if not needed.'),
        ('calibrationKey', 'str', "List of keys which trigger sensor calibration (space-separated list of keys, e.g. 'A B C ENTER')"),
        ('kalmanFilter', 'bool', "Whether to use Kalman filtering on the sensor data"),
        ('dataHistoryTime', 'float', "Number of seconds to keep the tracking data in memory (for delayed data usage)"),
        ('autoCalibration', 'bool', "Automatically re-calibrate the sensor each time it is activated"),
        ('playbackMode', 'bool', "Ignore real-time Mocap data and playback pre-recorded sensor data from CSV file"),
        ('playbackFile', 'str', "Full path and filename of the pre-recorded Mocap data (CSV or EMF file) to use"),
        ('rawSensorData', 'info', "Numpy array((3, 30)) of Reactor coordinates per sensor id"),
        ('sensors', 'info', "List of Sensor objects (see ReactorModule.py)"),
    ]
    
    def __init__(self, controller, initConfig=None, runConfigs=None):
        DrawableSourceModule.__init__(self, controller, initConfig, runConfigs)
                
        # init log file
        self.logActive = False
        for conf in self.runConfs.values():
            if conf['logToCSV']:
                # at least one configuration requires log to CSV
                self.logActive = True
                break
            
        if self.logActive:
            now = datetime.today()
            self.csvLogger = csv.writer(open(path.join(self.controller.gLogger.Path, now.strftime('%y%m%d%H%M%S_') + self.initConf['name'] +  '.csv') , 'w'), lineterminator = '\n')

        #Only playback mode?
        if len(self.initConf['IP']) > 0:
            self.playbackOnly = False  
        else: 
            self.playbackOnly = True

        # init mocap
        if not self.playbackOnly:
            ReactorHandler.connect(self.initConf['IP'], 6001, "eth0")
            ReactorHandler.start()
            ReactorHandler.startCapture()
        
        self.numSensors = self.initConf['nb_sensors']
        self.updateInterval = 1./self.initConf['updateFrequency']
        self.sensors = []            
        self.rawSensorData = np.zeros((3, 30))
        self.centroid = np.zeros(3)
        
        # Initializes the sensors
        self.sensors = [ Sensor(3, self.updateInterval, enableFilter=self.initConf['kalmanFilter']) for s in range(self.numSensors)]
        
        # Set up tracking of head position if needed
        self.rigidTrack = None
        cameraPosSens = self.initConf['cameraPositionSensors']
        if len(cameraPosSens) > 0:
            cameraPosSens = [int(sens) for sens in cameraPosSens.split(',')]
            print cameraPosSens
            self.rigidTrack = RigidTrack(cameraPosSens)
            
            
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
        
        # Head correction vector
        self.controller.registerKeyboardAction( 'G B', self.handlekey )
        self.headShift = np.array([0, 0, 0.4])
        
        # History of tracker data
        self.numHistorySlots = self.initConf['updateFrequency'] * self.initConf['dataHistoryTime']
        self.history = []
        
    def draw(self, window_width, window_height, eye=-1):
        DrawableSourceModule.draw(self, window_width, window_height, eye)
        
        glPushAttrib(GL_COLOR_BUFFER_BIT | GL_TEXTURE_BIT)
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(4, 0, 0, 4, -1, 2)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        
        ## display SENSORS
        glPointSize(10)
        glBegin(GL_POINTS)
        glColor3f(0.0, 1.0, 1.0)
        glVertex3f(self.centroid[0], self.centroid[2], 0)
        if np.isreal(self.rawSensorData).all() and self.rawSensorData.shape[1] >= self.numSensors:
            # Draw the (possibly filtered) sensordata
            glColor3f(1.0, 1.0, 0.0)
            for s in range(self.numSensors):
                pos = self.rawSensorData[:,s]
                glVertex3f(pos[0], pos[2], 0)
        glEnd()
        
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()
        glPopAttrib()
            
    def start(self, dt=0, duration=-1, configName=None):
        DrawableSourceModule.start(self, dt, configName)
        
        self._retrieveData(0)
        if self.activeConf['autoCalibration']:
            self.calibrate()
            
        self.controller.registerKeyboardAction( self.initConf['calibrationKey'], self.calibrate)
        pyglet.clock.schedule_interval(self._retrieveData, self.updateInterval)

    def stop(self, dt=0):
        DrawableSourceModule.stop(self, dt)
        pyglet.clock.unschedule(self._retrieveData)
        self.controller.unregisterKeyboardAction( self.initConf['calibrationKey'], self.calibrate )
        
    def cleanup(self):
        DrawableSourceModule.cleanup(self)
        
        if not self.playbackOnly:
            ReactorHandler.stopCapture()
            ReactorHandler.stop()
            ReactorHandler.disconnect()
        
        #close file handles
        #for k, v in self.playbackFiles:
        #    close(k)
        self.controller.unregisterKeyboardAction( 'G B', self.handlekey )
        
    def calibrate(self, key = ''):
        """
        Calibrate the position of the sensors tracking the head
        """
        if self.rigidTrack is not None:
            self.rigidTrack.set_reference(self.getPositions())
            self._retrieveData(0)
            self.log('Calibrated')
            
    def _retrieveData(self, dt):
        """
        Called at update frequency retrieve sensor data from the Mocap system
        """
        # Get current sample from mocap or pre-rec file
        if not self.activeConf['playbackMode']:
            self.rawSensorData = ReactorHandler.getAllSensors()
        else:
            self.rawSensorData = self.playbackFiles[self.activeConf['playbackFile']].next()
            
        # restrict to data for the sensors of interest     
        self.rawSensorData = self.rawSensorData[:, :self.numSensors]
        
        # compute centroid
        self.centroid = np.mean(self.rawSensorData,axis=1)
        if self.centroid.shape[0] < 3:
            self.centroid = np.zeros(3)
           
        # update sensors and their filters
        if np.isreal(self.rawSensorData).all() and self.rawSensorData.shape[1] >= self.numSensors:
            for s in range(self.numSensors):
                self.sensors[s].receiveData( self.rawSensorData[:,s] * np.array([-1, 1, -1]) )
                # update ne done after the recieve data for the Kallmann filter to be effective? bh.
                self.sensors[s].update()
                
        # store the data as history if needed
        if self.numHistorySlots > 0:
            if len(self.history) >= self.numHistorySlots:
                self.history.pop()
            self.history.insert(0, self.getPositions())
                
        # update camera position if wanted
        if self.rigidTrack:
            self.rigidTrack.set_current(self.getPositions())
            self.controller.gDisplay.set_camera_position(self.rigidTrack.T)
            self.controller.gDisplay.set_camera_rotation(self.rigidTrack.R)
            self.controller.gDisplay.set_camera_correction(self.headShift)
        
        #Only log if we're actively taking mocap input
        if self.logActive and self.activeConf['logToCSV'] and not self.activeConf['playbackMode']:
            # log times and location in experiment flow
            line = [ str("%.4f"%self.controller.gTimeManager.experimentTime()), self.controller._currentRoutine, self.controller._currentCondition]
            # log coordinates
            sensors = self.rawSensorData.transpose().tolist() #local var sensors
            line.extend([coord for sensor in sensors for coord in sensor])
            self.csvLogger.writerow(line)
    
    def getPositions(self, delay=0):
        """
        Returns a list of current positions of all sensors (in meters)
        """
        if delay > 0:
            index = int(delay / float(self.updateInterval))
            if len(self.history) > index:
                return self.history[index]
            else:
                self.log("History data requested that is not (yet) available (delay %s). Returning current data instead." % delay)
        positions = np.zeros((3, self.numSensors))
        for s in range(self.numSensors):
            positions[:,s] = self.sensors[s].getPosition() 
        return positions


    def getVelocities(self):
        """
        Returns a list of current velocities of all sensors (in m/s)
        """
        velocities = np.zeros((3, self.numSensors))
        for s in range(self.numSensors):
            velocities[:,s] = self.sensors[s].getVelocity() 
        return velocities

    def getAccelerations(self):
        """
        Returns a list of current accelerations of all sensors (in m/s^2)
        """
        accelerations = np.zeros((3, self.numSensors))
        for s in range(self.numSensors):
            accelerations[:,s] = self.sensors[s].getAcceleration() 
        return accelerations

    def getData(self):
        """
        For abstract interface (reactor is a source module). Keeping getPositions() for old calls to positions
        """
        DrawableSourceModule.getData(self)
        return self.getPositions()

    def getUpdateInterval(self):
        """
        For abstract interface (reactor is a source module). 
        """
        DrawableSourceModule.getUpdateInterval(self)
        return self.updateInterval

    def handlekey(self, keypressed = None):
        if keypressed == 'B':
            self.headShift[2] = self.headShift[2] - 0.1
        elif keypressed == 'G':
            self.headShift[2] = self.headShift[2] + 0.1
            
        print self.headShift
