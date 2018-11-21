'''
Created on Jan 29, 2011

@author: bh
@since: winter 2010

@license: Distributed under the terms of the GNU General Public License (GPL).
'''

from os import path
import csv
import threading, time
import socket, re

from datetime import datetime
from pyglet.gl import *
import numpy as np
from tracker.kalman import KalmanTracking

#pylnco modules
from display.tools import *
from abstract.AbstractClasses import DrawableSourceModule
from display.objloader import OBJ

def getMatrix(q):
    # compute matrix from quaternion
    mat = np.eye(3)
    mat[0,0] = (2.0 * q[0] * q[0]) + (2.0 * q[1] * q[1]) - 1.0
    mat[0,1] = (2.0 * q[1] * q[2]) + (2.0 * q[0] * q[3])
    mat[0,2] = (2.0 * q[1] * q[3]) - (2.0 * q[0] * q[2])
    mat[1,2] = (2.0 * q[2] * q[3]) + (2.0 * q[0] * q[1])
    mat[2,2] = (2.0 * q[0] * q[0]) + (2.0 * q[3] * q[3]) - 1.0
    return mat
    
def getEuler(m):
    # compute euler angles from matrix
    angles = np.zeros(3)
    angles[0] = math.atan2(m[1,2], m[2,2]) / math.pi * 180.0 
    angles[1] = math.asin(-m[0,2]) / math.pi * 180.0 
    angles[2] = math.atan2(m[0,1], m[0,0]) / math.pi * 180.0 
    return angles

    
def dbgData(dataFrame):
    body = dataFrame.RigidBodies[0]
    # print body
    print "id %d    " % body.id,
    print "x %.2f  y %.2f  z %.2f" % (body.x, body.y, body.z),
    print "qx %.2f  qy %.2f  qz %.2f  qw %.2f" % (body.qx, body.qy, body.qz, body.qw)

    
class ModuleMain(DrawableSourceModule):
    """
    A simple module to read data from NatNet protocol (OptiTrack sensors).
    
    Tracking software can be obtained here : http://www.naturalpoint.com/optitrack/downloads/tracking-tools.html
    
    Python bindings for the OptiTrack NatNet SDK can be obtained here : https://github.com/mkilling/PyNatNet
    """
    defaultInitConf = {
        'name': 'optitrack',
        'logToCSV': True,
        'kalmanFilter': False,
        'IP': ''
    }
    
    defaultRunConf = {
        'mirror': False,
        'delay': 0.0
    }
    
    confDescription = [
        ('name', 'str', "Your freespace tracker"),
        ('logToCSV', 'bool', "Save data to coma-separated-values file ( <modulename>_<date>.csv )"),
        ('kalmanFilter', 'bool', "Whether to use Kalman filtering on the sensor data"),  
        ('IP', 'str', "Network IP of the server computer (leave empty for localhost)"),
        ('mirror', 'bool', "Invert Y rotations"),        
        ('delay', 'float', "Delay in second"),  
        ('angles', 'info', "Euler angles (list of floats) of the sensor orientation."),
        ('getData()', 'info', "Get the array of raw data."),
    ]
    
    def __init__(self, controller, initConfig=None, runConfigs=None):
        DrawableSourceModule.__init__(self, controller, initConfig, runConfigs)
                
        # init 
        self.logActive = self.initConf['logToCSV']
        if self.logActive:
            now = datetime.today()
            self.csvLogger = csv.writer(open(path.join(self.controller.gLogger.Path, now.strftime('%y%m%d%H%M%S_') + self.initConf['name'] +  '.csv') , 'w'), lineterminator = '\n')
        
        # driver module
        import NatNet
        
        # init NatNet client
        self.client = NatNet.NatNetClient(1)
        if self.client is None:
            raise RuntimeError("Unable to instanciate the NatNet client for Optitrack.")   
        
        clientIP = socket.gethostbyname(socket.gethostname())
        # test validity of URL provided
        IPexpression = re.compile('\d+\.\d+\.\d+\.\d+').search(self.initConf['IP'])
        serverIP = IPexpression.group(0) if IPexpression is not None else clientIP
        
        if self.client.Initialize(clientIP, serverIP) != 0:
            raise RuntimeError("Failed to initialize NatNet client for Optitrack.")  
            
        # data debugging...
        # self.client.SetDataCallback(dbgData)
        
        # init internal variables
        self.angles = [0.0, 0.0, 0.0]
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
            self.kalmanTracker = KalmanTracking(4, [0.1, 0.1, 0.1, 0.1], 0.02, self.updateTime)
        else:
            self.kalmanTracker = None
            
    def draw(self, window_width, window_height, eye=-1):
        DrawableSourceModule.draw(self, window_width, window_height, eye)

        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glLightfv(GL_LIGHT0, GL_POSITION, vec4f([0.0, 0.0, 12.0, 0.0]))
        glLightfv(GL_LIGHT0, GL_AMBIENT, vecf(.03, .03, .03, 1))
        glLightfv(GL_LIGHT0, GL_DIFFUSE, vecf(.5, .5, .5, 1))
        glLightfv(GL_LIGHT0, GL_SPECULAR, vecf(.05, .05, .05, 1))
                
        ## display a 3D model moving with the sensor
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
        
        # setup delay and start updating
        self.frameDelay = int ( self.activeConf['delay'] / self.updateTime )
        pyglet.clock.schedule_interval(self.update, self.updateTime)  

    def stop(self, dt=0):
        DrawableSourceModule.stop(self, dt)
        pyglet.clock.unschedule(self.update)
        
    def cleanup(self):
        DrawableSourceModule.cleanup(self)
        
        # stop NatNet client
        if self.client.Uninitialize() < 0:
            raise RuntimeError("Failed to close NatNet client for Optitrack.")  
        
    def update(self, dt):
        """
        The update is called regularly to update angle data
        """
        if not self.started:
            return
            
        if self.client.lastFrame is None:
            return
        
        try:
            # get the last frame recieved by the NatNet client
            pos = np.array( [self.client.lastFrame.RigidBodies[0].x, self.client.lastFrame.RigidBodies[0].y, self.client.lastFrame.RigidBodies[0].z ])
            quat = np.array([self.client.lastFrame.RigidBodies[0].qx, self.client.lastFrame.RigidBodies[0].qy, self.client.lastFrame.RigidBodies[0].qz, self.client.lastFrame.RigidBodies[0].qw] )
            
            # use the next index to write into
            self.writeIndex = (self.writeIndex + 1) % (self.maxFrameDelay + 1)
            # read data from thread and immediately let it continue
            if self.kalmanTracker is None:
                self.data[self.writeIndex] = quat
            else:
                self.kalmanTracker.observe(quat)
                self.kalmanTracker.predict()
                self.data[self.writeIndex] = self.kalmanTracker.X
            
            # set index for reading the former data
            readIndex = (self.writeIndex - self.frameDelay) % (self.maxFrameDelay + 1)
            
            # fill in the angle array from data reading index          
            if np.isreal(self.data[readIndex]).all():
                a = getEuler(getMatrix(self.data[readIndex]))
                self.angles[0] = a[2] 
                self.angles[1] = -a[1]
                self.angles[2] = -a[0] 
                
            # compute mirror if requested
            if self.activeConf['mirror']:
                self.angles[1] = -self.angles[1]
                self.angles[0] = -self.angles[0]
        except:
            print 'Error reading OptiTrack data'
        
        # fill in logs if required
        if self.logActive:
            # log time
            line = [ str("%.4f"%self.controller.gTimeManager.experimentTime()), self.controller._currentRoutine, self.controller._currentCondition ]
            # log coordinates
            line.extend(self.angles)
            self.csvLogger.writerow(line)


    def getData(self):
        """
        For abstract interface (reactor is a source module). Keeping getPositions() for old calls to positions
        """
        DrawableSourceModule.getData(self)
        return self.client.lastFrame

    def getUpdateInterval(self):
        """
        For abstract interface (reactor is a source module). 
        """
        return self.updateTime
    