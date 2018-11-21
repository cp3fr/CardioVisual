"""
Module for displaying a stick that is moved by two mocap sensors

@author: Tobias Leugger
@since: Winter 2011
"""

from pyglet.gl import *
import numpy as np

from abstract.AbstractClasses import DrawableModule
from controller import getPathFromString
from display.objloader import OBJ
from display.tools import vecf, vec4f


class ModuleMain(DrawableModule):
    """
    Module for displaying a stick that is moved by two mocap sensors
    """
    defaultInitConf = {
        'name': 'stick',
        'stickMesh': '$EXPYVRROOT$/lncocomponents/tracker/stick/stick.obj',
        'sensorNumbers': '0,1',
        'calibrationKey': 'V',
        'trackerModuleName': 'reactor',
    }
    
    defaultRunConf = {
        'delay': 0.,
        'calibrationX': 0.,
        'calibrationY': 0.,
        'calibrationZ': 0.,
    }
    
    confDescription = [
        ('name', 'str', "Name of this component"),
        ('stickMesh', 'str', "Location of the obj to use as the stick"),
        ('sensorNumbers', 'str', "Comma separated list of the two sensors to use for tracking the stick position"),
        ('calibrationKey', 'str', "List of keys which trigger sensor calibration (space-separated list of keys, e.g. 'A B C ENTER')"),
        ('trackerModuleName', 'str', "Name of the reactor tracker module to get the sensor data from"),
        ('delay', 'float', "Delay with which to get the sensor data"),
        ('calibrationX', 'float', "X position to reset the tip of the stick to when the calibration key is pressed"),
        ('calibrationY', 'float', "Y position to reset the tip of the stick to when the calibration key is pressed"),
        ('calibrationZ', 'float', "Z position to reset the tip of the stick to when the calibration key is pressed"),
    ]
    
    def __init__(self, controller, initConfig=None, runConfigs=None):
        DrawableModule.__init__(self, controller, initConfig, runConfigs)
        self.sensorNums = [int(num) for num in self.initConf['sensorNumbers'].split(',')]
        self.calibPos = np.array((0., 0., 0.))
        
        # Load stick mesh
        self.stick = OBJ(getPathFromString(self.initConf['stickMesh']))
        
        # Generate prerender list
        # TODO: put these things somewhere else?
        lightPos = [ [1.5, 0.8, 2.0, 1.0], [1.9, 1.85, 6.0, 1.0] ]
        self.prerenderList = glGenLists(1)
        glNewList(self.prerenderList, GL_COMPILE)
        glColor3f(1, 1, 1)
        glEnable(GL_DEPTH_TEST)
        
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glLightfv(GL_LIGHT0, GL_POSITION, vec4f(lightPos[0]))
        glLightfv(GL_LIGHT0, GL_AMBIENT, vecf(.3, .3, .3, 1))
        glLightfv(GL_LIGHT0, GL_DIFFUSE, vecf(.75, .75, .75, 1))
        glLightfv(GL_LIGHT0, GL_SPECULAR, vecf(.85, .85, .8, 1))
        glLightf(GL_LIGHT0, GL_CONSTANT_ATTENUATION, 1.0)
        glLightf(GL_LIGHT0, GL_LINEAR_ATTENUATION, 0.005)
        glLightf(GL_LIGHT0, GL_QUADRATIC_ATTENUATION, 0.01)
        
        glEnable(GL_LIGHT1)
        glLightfv(GL_LIGHT1, GL_POSITION, vec4f(lightPos[1]))
        glLightfv(GL_LIGHT1, GL_AMBIENT, vecf(.2, .2, .2, 1))
        glLightfv(GL_LIGHT1, GL_DIFFUSE, vecf(.5, .5, .5, 1))
        glLightfv(GL_LIGHT1, GL_SPECULAR, vecf(0.9, 0.9, 0.9, 1))
        glLightf(GL_LIGHT1, GL_CONSTANT_ATTENUATION, 1.0)
        glLightf(GL_LIGHT1, GL_LINEAR_ATTENUATION, 0.01)
        glLightf(GL_LIGHT1, GL_QUADRATIC_ATTENUATION, 0.0051)
        glEndList()
        
    def draw(self, window_width, window_height, eye=-1):
        DrawableModule.draw(self, window_width, window_height, eye)
        
        # Get the sensor position from the reactor module
        pos = self.controller.gModuleList[self.initConf['trackerModuleName']].getPositions(delay=self.activeConf['delay'])
        pos0 = pos[:,self.sensorNums[0]] - self.calibPos
        pos1 = pos[:,self.sensorNums[1]] - self.calibPos
        
        glPushAttrib(GL_ALL_ATTRIB_BITS)
        
        # Execute the prerender list
        glCallList(self.prerenderList)
        

        
        # Calculate position and angle of stick
        glTranslatef(pos0[0], pos0[1], pos0[2])
        stickVec = pos1 - pos0
        stickVec /= np.linalg.norm(stickVec)
        meshVec = np.array((0., -1., 0.))
        rotVec = np.cross(meshVec, stickVec)
        angle = np.arccos(np.dot(meshVec, stickVec))/np.pi*180.
        glRotatef(angle, rotVec[0], rotVec[1], rotVec[2])
        
        #scale the stick by an arbitrary factor (UGLY!!)
        #glScalef(0.35,0.35,0.35)
        
        
        # Draw the stick
        
        glCallList(self.stick.gl_list)
        glPopAttrib()
            
    def start(self, dt=0, duration=-1, configName=None):
        DrawableModule.start(self, dt, duration, configName)
        self.controller.registerKeyboardAction(self.initConf['calibrationKey'], self.calibrate)

    def stop(self, dt=0):
        DrawableModule.stop(self, dt)
        self.controller.unregisterKeyboardAction(self.initConf['calibrationKey'], self.calibrate)
        
    def calibrate(self, key = ''):
        """
        Calibrate the position of the sensors tracking the stick
        """
        pos = self.controller.gModuleList[self.initConf['trackerModuleName']].getPositions()
        self.calibPos = pos[:,self.sensorNums[0]]
        self.calibPos -= self.activeConf['calibrationX'], self.activeConf['calibrationY'], self.activeConf['calibrationZ']


