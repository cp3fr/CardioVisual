'''
Read or playback (pre-recorded file) motion capture data from a robotic end effector system

@author: Nathan
@since: Spring 2011

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
from tracker.StrokeRobotHandler import StrokeRobotHandler
from controller import getPathFromString


class ModuleMain(DrawableSourceModule):
    """
    A simple module to log the data from Stroke Robot end effector  into CSV file
    (and also log key press as triggers)
    """
    defaultInitConf = {
        'name': 'strokerobot',
        'IP': '192.168.9.100',
        'tcpPort': 4444,
        'udpPort': 5555,        
        'updateFrequency': 100,
        'kalmanFilter': False
    }
    
    defaultRunConf = {
        'playbackMode': False,
        'playbackFile': 'playback_filename.csv',
        'logToCSV': True,
    }
    
    confDescription = [
        ('name', 'str', "Stroke Robot End Effector"),
        ('IP', 'str', "IP address of the computer running stroke robot server. Leave empty if all conditions are only playback"),
        ('tcpPort', 'int', "Port for TCP communication"),
        ('udpPort', 'int', "Port for UDP communication"),
        ('logToCSV', 'bool', "Save raw sensor data to comma-separated-values file ( <modulename>_<date>.csv )"),
        ('updateFrequency', 'float', "Frequency (in Hz) to retrieve the sensor data"),
        ('kalmanFilter', 'bool', "Whether to use Kalman filtering on the sensor data"),
        ('playbackMode', 'bool', "Ignore real-time Mocap data and playback pre-recorded sensor data from CSV file"),
        ('playbackFile', 'str', "Full path and filename of the pre-recorded Mocap data (CSV or EMF file) to use")
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
            self.sRobot = StrokeRobotHandler(self.initConf['IP'], self.initConf['tcpPort'], self.initConf['udpPort'], "eth0")
        else: 
            self.sRobot = None
        
        self.updateInterval = 1./self.initConf['updateFrequency']          
        self.rawSensorData = np.zeros(3)
        
        # Initializes the sensors
        self.sensor = Sensor(3, self.updateInterval, enableFilter=self.initConf['kalmanFilter'])
            
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
                        
        #Visual feedback
        self.sphere = gluNewQuadric()
        gluQuadricNormals(self.sphere, GLU_SMOOTH)

                
    def draw(self, window_width, window_height, eye=-1):
        DrawableSourceModule.draw(self, window_width, window_height, eye)
    
        glColor3f(0.0,0.0,1.0)  #blue
        pos = self.rawSensorData[:]
        glTranslatef(pos[0], pos[1], pos[2])
        gluSphere(self.sphere,0.2,30,30)
        glTranslatef(-pos[0], -pos[1], -pos[2])

            
    def start(self, dt=0, duration=-1, configName=None):
        DrawableSourceModule.start(self, dt, configName)        
        if not self.sRobot is None:
            self.sRobot.start()
        self._retrieveData(0)
        pyglet.clock.schedule_interval(self._retrieveData, self.updateInterval)

    def stop(self, dt=0):
        DrawableSourceModule.stop(self, dt)
        if not self.sRobot is None:
            self.sRobot.stop()
        pyglet.clock.unschedule(self._retrieveData)
        
    def cleanup(self):
        DrawableSourceModule.cleanup(self)
        
        if not self.playbackOnly:
            self.sRobot.stop()
            self.sRobot.disconnect()
        
    def _retrieveData(self, dt):
        """
        Called at update frequency retrieve sensor data from the stroking robot system
        """
        # Get current sample from mocap or pre-rec file
        if not self.activeConf['playbackMode']:
            self.rawSensorData = self.sRobot.getAllSensors()
        else:
            self.rawSensorData = self.playbackFiles[self.activeConf['playbackFile']].next()
                               
        # update sensors and their filters
        self.sensor.receiveData( self.rawSensorData[:]) # * np.array([-1, 1, -1]) )     
        self.sensor.update()
                
        #Only log if we're actively taking mocap input
        if self.logActive and self.activeConf['logToCSV'] and not self.activeConf['playbackMode']:
            # log times
            line = [self.controller.gTimeManager.experimentTime()]
            # log coordinates
            sensors = self.rawSensorData.transpose().tolist() #local var sensors
            line.extend([coord for sensor in sensors])
            self.csvLogger.writerow(line)
    
            
    def getPositions(self):
        """
        Returns a list of current positions of all sensors (in meters)
        """
        positions = np.zeros(3)
        positions = self.sensor.getPosition() 
        return positions

    def getVelocities(self):
        """
        Returns a list of current velocities of all sensors (in m/s)
        """
        velocities = np.zeros(3)
        velocities = self.sensor.getVelocity() 
        return velocities

    def getAccelerations(self):
        """
        Returns a list of current accelerations of all sensors (in m/s^2)
        """
        accelerations = np.zeros(3)
        accelerations = self.sensor.getAcceleration() 
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


